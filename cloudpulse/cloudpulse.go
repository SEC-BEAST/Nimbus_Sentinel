package main

import (
	"bufio"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"time"
	"path/filepath"
)

const (
	serverURL = "http://localhost:5000/logs" // Mock server to send logs
	systemdLogScript = "extract_systemd_logs.sh" // Path to systemd log extraction script
)

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
			go sendLog(line)
		}
		time.Sleep(1 * time.Second) // Prevent excessive CPU usage
	}
}

func sendLog(logLine string) {
	resp, err := http.Post(serverURL, "text/plain", bufio.NewReaderString(logLine))
	if err != nil {
		log.Printf("Failed to send log: %v", err)
		return
	}
	defer resp.Body.Close()
	fmt.Println("Log sent successfully")
}
