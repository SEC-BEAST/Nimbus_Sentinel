package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
)

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

func main() {
	// Read log input from user
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Enter a log message: ")
	logMessage, _ := reader.ReadString('\n')

	// Clean the log message
	cleanedLog := cleanLogMessage(logMessage)

	// Print the cleaned log
	fmt.Println("Cleaned Log:", cleanedLog)
}
