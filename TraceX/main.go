package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"regexp"
	"strings"
	"sync"
	"time"
)

// Data Structures for Tracking Attacks
var (
	failedLogins       = make(map[string][]time.Time)
	requestCounts      = make(map[string]int)
	portScans          = make(map[string]map[string]struct{})
	privilegeEscalation = make(map[string][]time.Time)
	malwareSignatures  = []string{"crypto-miner", "ransomware", "botnet"}
	mu                 sync.Mutex
)

const LOGSTASH_URL = "http://localhost:5044"

// LogData Struct
type LogData struct {
	Message   string `json:"message"`
	SourceIP  string `json:"source_ip"`
	Timestamp string `json:"timestamp"`
}

// Main Function to Process Logs
func processLog(w http.ResponseWriter, r *http.Request) {
	var logData LogData
	err := json.NewDecoder(r.Body).Decode(&logData)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	message := strings.ToLower(logData.Message)
	ip := logData.SourceIP
	timestamp := time.Now()

	mu.Lock() // Lock for thread safety
	defer mu.Unlock()

	// 🚨 Brute Force Detection
	if strings.Contains(message, "failed password") || strings.Contains(message, "authentication failure") {
		failedLogins[ip] = append(failedLogins[ip], timestamp)
		filtered := filterTimestamps(failedLogins[ip], 1*time.Minute)
		failedLogins[ip] = filtered
		if len(failedLogins[ip]) > 5 {
			sendAlert("🚨 Brute Force Attack Detected!", ip)
		}
	}

	// 🚨 Unauthorized SSH Access
	if strings.Contains(message, "ssh error") {
		sendAlert("⚠️ Unauthorized SSH Access Attempt", ip)
	}

	// 🚨 DDoS Attack Detection
	requestCounts[ip]++
	if requestCounts[ip] > 100 {
		sendAlert("🚨 Possible DDoS Attack!", ip)
		requestCounts[ip] = 0
	}

	// 🚨 Port Scanning Detection
	if strings.Contains(message, "connection attempt") {
		port := extractPort(message)
		if port != "" {
			if _, exists := portScans[ip]; !exists {
				portScans[ip] = make(map[string]struct{})
			}
			portScans[ip][port] = struct{}{}
			if len(portScans[ip]) > 10 {
				sendAlert("🚨 Port Scanning Detected!", ip)
				portScans[ip] = make(map[string]struct{})
			}
		}
	}

	// 🚨 Privilege Escalation Attempt
	if strings.Contains(message, "sudo:") && strings.Contains(message, "authentication failure") {
		privilegeEscalation[ip] = append(privilegeEscalation[ip], timestamp)
		filtered := filterTimestamps(privilegeEscalation[ip], 5*time.Minute)
		privilegeEscalation[ip] = filtered
		if len(privilegeEscalation[ip]) > 3 {
			sendAlert("🚨 Privilege Escalation Attempt!", ip)
		}
	}

	// 🚨 Malware Detection
	for _, malware := range malwareSignatures {
		if strings.Contains(message, malware) {
			sendAlert(fmt.Sprintf("🚨 Possible Malware Activity Detected (%s)", malware), ip)
		}
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprintln(w, `{"status": "Log processed"}`)
}

// Utility Functions

func sendAlert(alertType, ip string) {
	alert := map[string]string{
		"timestamp": time.Now().Format(time.RFC3339),
		"alert":     alertType,
		"ip":        ip,
	}
	alertJSON, _ := json.Marshal(alert)
	http.Post(LOGSTASH_URL, "application/json", strings.NewReader(string(alertJSON)))
	fmt.Printf("⚠️ %s from %s\n", alertType, ip)
}

func filterTimestamps(timestamps []time.Time, duration time.Duration) []time.Time {
	threshold := time.Now().Add(-duration)
	var filtered []time.Time
	for _, t := range timestamps {
		if t.After(threshold) {
			filtered = append(filtered, t)
		}
	}
	return filtered
}

func extractPort(message string) string {
	re := regexp.MustCompile(`port (\d+)`)
	match := re.FindStringSubmatch(message)
	if len(match) > 1 {
		return match[1]
	}
	return ""
}

// Main Function
func main() {
	http.HandleFunc("/process-log", processLog)
	fmt.Println("🚀 Log Processor running on http://0.0.0.0:5000")
	log.Fatal(http.ListenAndServe(":5000", nil))
}
