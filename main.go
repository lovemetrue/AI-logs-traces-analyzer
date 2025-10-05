package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

func main() {
	// Запускаем два сервера:
	// - 8080 для OTLP данных из кластера
	// - 8081 для UI/API запросов
	
	go startOTLPServer()  // порт 8080
	startAPIServer()      // порт 8081
}

func startOTLPServer() {
	router := gin.New()
	router.Use(gin.Recovery())
	
	// OTLP endpoints для приема данных из кластера
	router.POST("/otlp/v1/traces", handleOTLPTraces)
	router.POST("/otlp/v1/metrics", handleOTLPMetrics)
	router.POST("/otlp/v1/logs", handleOTLPLogs)
	
	// Health check для otelier
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy", "service": "otlp-receiver"})
	})

	log.Printf("Starting OTLP receiver on :8080")
	if err := router.Run(":8080"); err != nil {
		log.Fatalf("OTLP server failed: %v", err)
	}
}

func startAPIServer() {
	router := gin.Default()
	
	// API endpoints для UI и ручных запросов
	router.GET("/api/health", handleHealth)
	router.POST("/api/analyze/incident", handleIncidentAnalysis)
	router.POST("/api/analyze/text", handleTextAnalysis)
	router.GET("/api/traces/search", handleTraceSearch)
	router.GET("/api/logs/search", handleLogSearch)
	
	// Статус системы
	router.GET("/api/system/status", handleSystemStatus)

	log.Printf("Starting API server on :8081")
	if err := router.Run(":8081"); err != nil {
		log.Fatalf("API server failed: %v", err)
	}
}

// Обработчик для OTLP трейсов
func handleOTLPTraces(c *gin.Context) {
	// Проверяем аутентификацию
	authToken := c.GetHeader("x-auth-token")
	if authToken != os.Getenv("OTLP_AUTH_TOKEN") {
		c.JSON(401, gin.H{"error": "unauthorized"})
		return
	}
	
	clusterName := c.GetHeader("x-cluster-name")
	
	var traceData map[string]interface{}
	if err := c.BindJSON(&traceData); err != nil {
		log.Printf("Error parsing traces from cluster %s: %v", clusterName, err)
		c.JSON(400, gin.H{"error": "invalid trace data"})
		return
	}
	
	log.Printf("Received traces from %s: %d spans", clusterName, estimateSpanCount(traceData))
	
	// Асинхронная обработка
	go processIncomingTraces(clusterName, traceData)
	
	c.JSON(200, gin.H{"status": "accepted"})
}

// Обработчик для OTLP логов
func handleOTLPLogs(c *gin.Context) {
	authToken := c.GetHeader("x-auth-token")
	if authToken != os.Getenv("OTLP_AUTH_TOKEN") {
		c.JSON(401, gin.H{"error": "unauthorized"})
		return
	}
	
	clusterName := c.GetHeader("x-cluster-name")
	
	var logData map[string]interface{}
	if err := c.BindJSON(&logData); err != nil {
		log.Printf("Error parsing logs from cluster %s: %v", clusterName, err)
		c.JSON(400, gin.H{"error": "invalid log data"})
		return
	}
	
	log.Printf("Received logs from %s: %d entries", clusterName, estimateLogCount(logData))
	
	go processIncomingLogs(clusterName, logData)
	
	c.JSON(200, gin.H{"status": "accepted"})
}

// Обработчик для метрик
func handleOTLPMetrics(c *gin.Context) {
	authToken := c.GetHeader("x-auth-token")
	if authToken != os.Getenv("OTLP_AUTH_TOKEN") {
		c.JSON(401, gin.H{"error": "unauthorized"})
		return
	}
	
	clusterName := c.GetHeader("x-cluster-name")
	
	var metricData map[string]interface{}
	if err := c.BindJSON(&metricData); err != nil {
		log.Printf("Error parsing metrics from cluster %s: %v", clusterName, err)
		c.JSON(400, gin.H{"error": "invalid metric data"})
		return
	}
	
	go processIncomingMetrics(clusterName, metricData)
	
	c.JSON(200, gin.H{"status": "accepted"})
}