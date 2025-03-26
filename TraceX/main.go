package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"time"
)

// LogData represents the structure of the incoming logs.
type LogData struct {
	Message   string `json:"message"`
	Source    string `json:"source"`
	Timestamp string `json:"timestamp"`
	Cloud     string `json:"cloud"`
}

// AlertData represents the structure of generated alerts.
type AlertData struct {
	Timestamp string `json:"timestamp"`
	AlertType string `json:"alert_type"`
	Details   string `json:"details"`
}

// ANSI color codes for terminal output.
const (
	RedColor   = "\033[31m"
	ResetColor = "\033[0m" // Reset to default terminal color
)

var (
	logChannel   = make(chan LogData, 100)
	alertChannel = make(chan AlertData, 100)
)

// processLog handles incoming logs and sends them to the logChannel for processing.
func processLog(w http.ResponseWriter, r *http.Request) {
	var logData LogData
	err := json.NewDecoder(r.Body).Decode(&logData)
	if err != nil {
		http.Error(w, "Invalid JSON format", http.StatusBadRequest)
		return
	}

	// Send the log to the logChannel for further processing.
	logChannel <- logData

	// Respond to the sender
	w.Header().Set("Content-Type", "application/json")
	response := map[string]string{"status": "Log processed"}
	json.NewEncoder(w).Encode(response)
}

// analyzeLog processes logs and sends alerts/errors to the alertChannel.
func analyzeLog(logData LogData) {
	// Define patterns to detect attacks or errors
	errorPattern := regexp.MustCompile(`(?i)error|fail|denied|critical|unauthorized`)
	attackPattern := regexp.MustCompile(`(?i)attack|intrusion|sql injection|xss|malware`)

	// Check if the log contains error-related keywords
	if errorPattern.MatchString(logData.Message) {
		alertChannel <- AlertData{
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			AlertType: "Error Detected",
			Details:   logData.Message,
		}
	}

	// Check if the log contains attack-related keywords
	if attackPattern.MatchString(logData.Message) {
		alertChannel <- AlertData{
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			AlertType: "Potential Attack",
			Details:   logData.Message,
		}
	}
}

// startLogPrinter continuously prints incoming logs to the console.
func startLogPrinter() {
	for logData := range logChannel {
		fmt.Printf("Incoming Log: %+v\n", logData)
		analyzeLog(logData)
	}
}

// startAlertPrinter continuously prints alerts/errors to the console in red color.
func startAlertPrinter() {
	for alert := range alertChannel {
		fmt.Printf("%sGenerated Alert: %+v%s\n", RedColor, alert, ResetColor)
	}
}

func main() {
	// Set up the HTTP server
	http.HandleFunc("/process-log", processLog)

	// Start separate goroutines for logs and alerts
	go startLogPrinter() // This goroutine handles incoming logs
	go startAlertPrinter() // This goroutine handles alerts/errors

	// Start the server
	fmt.Println("Starting Log Processor on http://0.0.0.0:5000")
	err := http.ListenAndServe(":5000", nil)
	if err != nil {
		fmt.Printf("Failed to start server: %v\n", err)
	}
}
