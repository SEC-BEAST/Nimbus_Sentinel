package main

import (
	"bufio"
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"regexp"  // Added for regex-based filtering
	"strings" // Added for string manipulation
	"time"

	_ "github.com/lib/pq" // PostgreSQL driver
)

const (
	serverURL        = "http://172.16.110.252:5000/process-log" // Mock server to send logs
	systemdLogScript = "extract_systemd_logs.sh"                // Path to systemd log extraction script
	dbUser           = "postgres"
	dbPassword       = "yourpassword"
	dbName           = "cloudpulse"
	dbHost           = "localhost"
	dbPort           = "5432"
)

var db *sql.DB
var outputMode string

var defaultLogPaths = []string{
	"/var/log/syslog",
	"/var/log/auth.log",
	"/var/log/nginx/access.log",
	"/var/log/nginx/error.log",
	"/var/log/apache2/access.log",
	"/var/log/apache2/error.log",
	"/var/log/keystone/keystone.log",
	"/var/log/nova/nova-api.log",
	"/var/log/nova/nova-compute.log",
	"/var/log/glance/glance-api.log",
	"/var/log/glance/glance-registry.log",
	"/var/log/cinder/cinder-api.log",
	"/var/log/cinder/cinder-volume.log",
	"/var/log/neutron/neutron-server.log",
	"/var/log/neutron/neutron-l3-agent.log",
	"/var/log/neutron/neutron-dhcp-agent.log",
	"/var/log/neutron/neutron-metadata-agent.log",
	"/var/log/horizon/horizon.log",
	"/var/log/ceilometer/ceilometer-agent.log",
	"/var/log/heat/heat-api.log",
	"/var/log/heat/heat-engine.log",
}

func main() {
	// Ensure systemd service is set up before anything else
	setupSystemdService()

	fmt.Println("Choose log destination:")
	fmt.Println("1. Send to HTTP Server")
	fmt.Println("2. Save to Local File")
	fmt.Println("3. Store in Database")
	fmt.Scanln(&outputMode)

	var logFilePath string
	fmt.Println("Choose log source:")
	fmt.Println("1. Auto-detect logs")
	fmt.Println("2. Enter custom log path")
	var choice int
	fmt.Scanln(&choice)

	if choice == 1 {
		logFilePath = detectLogFile()
		if logFilePath == "" {
			fmt.Println("No logs found in standard locations. Running systemd log extraction...")
			runSystemdLogExtraction()
			logFilePath = detectLogFile()
		}
	} else {
		fmt.Print("Enter custom log path: ")
		fmt.Scanln(&logFilePath)
	}

	if logFilePath == "" {
		log.Fatal("No valid log file found!")
	}

	monitorLogFile(logFilePath)
}

func detectLogFile() string {
	for _, path := range defaultLogPaths {
		if _, err := os.Stat(path); err == nil {
			fmt.Println("Detected log file:", path)
			return path
		}
	}
	return ""
}

func runSystemdLogExtraction() {
	cmd := exec.Command("/bin/bash", systemdLogScript)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Failed to extract systemd logs:", err)
	}
}

func setupSystemdService() {
	cmd := exec.Command("/bin/bash", "setup_systemd_service.sh")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Failed to set up systemd service:", err)
	}
}

// Function to monitor a log file and process new lines
func monitorLogFile(logFilePath string) {
	file, err := os.Open(logFilePath)
	if err != nil {
		log.Fatalf("Error opening log file: %v", err)
	}
	defer file.Close()

	file.Seek(0, os.SEEK_END) // Move to end of file like `tail -f`
	reader := bufio.NewReader(file)

	for {
		line, err := reader.ReadString('\n')
		if err == nil {
			// Extract timestamp from the log entry
			extractedTimestamp := extractTimestamp(line)

			// Define `cleanedMessage` by calling `cleanLogMessage(line)`
			cleanedMessage := cleanLogMessage(line)

			logEntry := map[string]string{
				"timestamp": extractedTimestamp, // Use extracted timestamp
				"message":   cleanedMessage,
				"source":    logFilePath,
				"cloud":     "openstack",
			}

			jsonData, err := json.Marshal(logEntry)
			if err != nil {
				log.Printf("Failed to encode log as JSON: %v", err)
				continue
			}

			// Output handling
			switch outputMode {
			case "1":
				sendToHTTP(jsonData)
			case "2":
				writeToFile(jsonData)
			case "3":
				saveToDatabase(logEntry)
			default:
				log.Println("Invalid output mode. Defaulting to HTTP.")
				sendToHTTP(jsonData)
			}
		}
		time.Sleep(1 * time.Second)
	}
}

// Function to send log data to an HTTP server
func sendToHTTP(jsonData []byte) {
	// Channel to signal animation to stop
	done := make(chan bool)

	// Start animation in a separate goroutine
	go func() {
		dots := []string{".  ", ".. ", "..."}
		i := 0
		for {
			select {
			case <-done:
				fmt.Print("\r\033[K") // Clear animation before exiting
				return
			default:
				fmt.Printf("\rSending logs%s", dots[i%len(dots)])
				i++
				time.Sleep(500 * time.Millisecond)
			}
		}
	}()

	// Send the log
	resp, err := http.Post(serverURL, "application/json", bytes.NewBuffer(jsonData))
	close(done) // Stop animation

	if err != nil {
		fmt.Println("\rFailed to send log to HTTP.") // Ensure proper output
		log.Printf("Error: %v", err)
		return
	}
	defer resp.Body.Close()

	// Print final success message
	//fmt.Println("\rLog sent successfully!      ") // Clears animation
}

func writeToFile(jsonData []byte) {
	file, err := os.OpenFile("cloudpulse_logs.json", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Failed to open log file: %v", err)
		return
	}
	defer file.Close()

	_, err = file.WriteString(string(jsonData) + "\n")
	if err != nil {
		log.Printf("Failed to write log to file: %v", err)
		return
	}

	fmt.Println("Log saved to file successfully")
}

func saveToDatabase(logData map[string]string) {
	if db == nil {
		connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
			dbHost, dbPort, dbUser, dbPassword, dbName)
		var err error
		db, err = sql.Open("postgres", connStr)
		if err != nil {
			log.Fatalf("Failed to connect to database: %v", err)
		}
	}

	_, err := db.Exec("INSERT INTO logs (timestamp, message, source, cloud) VALUES ($1, $2, $3, $4)",
		logData["timestamp"], logData["message"], logData["source"], logData["cloud"])

	if err != nil {
		log.Printf("Failed to insert log into database: %v", err)
		return
	}

	fmt.Println("Log stored in database successfully")
}

// cleanLogMessage removes ANSI escape sequences and extracts the core log message.
func cleanLogMessage(rawMessage string) string {
	// Step 1: Normalize ANSI codes (handles both \x1b and #033 notations)
	ansiEscape := regexp.MustCompile(`(\x1b|\#033)\[[0-9;]*[mK]`)
	cleanedMessage := ansiEscape.ReplaceAllString(rawMessage, "")

	// Step 2: Correct regex to extract log fields
	logPattern := regexp.MustCompile(`(?P<Service>\S+)\[(?P<PID>\d+)\]:\s*(?P<Level>DEBUG|INFO|WARNING|ERROR)\s+(?P<Component>[\w\d\._]+)\s+(?P<Message>.*?)(?P<Metadata>\{\{.*\}\})?$`)

	// Step 3: Extract matches
	matches := logPattern.FindStringSubmatch(cleanedMessage)

	// Step 4: If regex matches, format the cleaned log
	if len(matches) > 0 {
		service := matches[1]
		pid := matches[2]
		level := matches[3]
		component := matches[4]
		message := strings.TrimSpace(matches[5])
		metadata := strings.TrimSpace(matches[6])

		if metadata != "" {
			return fmt.Sprintf("%s[%s]:%s %s , %s, %s", service, pid, level, component, message, metadata)
		}
		return fmt.Sprintf("%s[%s]:%s %s , %s", service, pid, level, component, message)
	}

	// If regex does not match, return a fallback cleaned message
	return strings.TrimSpace(cleanedMessage)
}

// Function to extract and clean the log timestamp
func extractTimestamp(rawMessage string) string {
	// Regex to match timestamp (e.g., 2025-03-25T20:47:36.731131+05:30)
	timestampPattern := regexp.MustCompile(`^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2})`)

	matches := timestampPattern.FindStringSubmatch(rawMessage)
	if len(matches) > 1 {
		return matches[1] // Extracted timestamp
	}

	// If no valid timestamp is found, fallback to current time (optional)
	return time.Now().Format(time.RFC3339)
}
