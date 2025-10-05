// vector_db.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/amikos-tech/chroma-go"
)

type VectorDBClient struct {
	client *chroma.Client
}

func NewVectorDBClient(host string) (*VectorDBClient, error) {
	client, err := chroma.NewClient(host)
	if err != nil {
		return nil, err
	}
	return &VectorDBClient{client: client}, nil
}

func (v *VectorDBClient) SaveTraces(traceData map[string]interface{}) error {
	collection, err := v.client.GetOrCreateCollection("traces", nil)
	if err != nil {
		return err
	}
	
	// Преобразуем трейсы в векторное представление
	documents, metadatas, ids, embeddings := processTracesForVectorDB(traceData)
	
	_, err = collection.Add(
		context.Background(),
		chroma.NewAddEmbeddings(embeddings).
			WithDocuments(documents).
			WithMetadatas(metadatas).
			WithIDs(ids),
	)
	
	return err
}

func (v *VectorDBClient) SearchSimilarIssues(query string, limit int) ([]SearchResult, error) {
	collection, err := v.client.GetCollection("traces")
	if err != nil {
		return nil, err
	}
	
	// Получаем эмбеддинг для запроса
	queryEmbedding, err := getEmbedding(query)
	if err != nil {
		return nil, err
	}
	
	results, err := collection.Query(
		context.Background(),
		chroma.NewQueryEmbeddings([][]float32{queryEmbedding}).
			WithNResults(limit).
			WithInclude([]string{"metadatas", "documents", "distances"}),
	)
	
	if err != nil {
		return nil, err
	}
	
	return convertToSearchResults(results), nil
}