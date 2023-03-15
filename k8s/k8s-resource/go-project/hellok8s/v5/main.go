package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
)

func hello(w http.ResponseWriter, r *http.Request) {
	host, _ := os.Hostname()
	dbURL := os.Getenv("DB_URL")
	dbPassword := os.Getenv("DB_PASSWORD")
	io.WriteString(w, fmt.Sprintf("[v5] Hello, Kubernetes! From host: %s, Get Database Connect URL: %s By PASSWORD: %s", host, dbURL, dbPassword))
}

func main() {
	http.HandleFunc("/", hello)
	http.ListenAndServe(":3000", nil)
}
