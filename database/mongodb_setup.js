// FloatChat ARGO MongoDB Setup Script
// Run with: mongo floatchat < mongodb_setup.js

// Switch to floatchat database
use floatchat;

// Create collections with validation
db.createCollection("chat_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "query", "response", "timestamp"],
            properties: {
                user_id: {
                    bsonType: "int",
                    description: "User ID must be an integer"
                },
                query: {
                    bsonType: "string",
                    description: "User query must be a string"
                },
                response: {
                    bsonType: "string", 
                    description: "Bot response must be a string"
                },
                timestamp: {
                    bsonType: "date",
                    description: "Timestamp must be a date"
                },
                relevant_docs: {
                    bsonType: ["array"],
                    description: "Relevant documents from vector search"
                }
            }
        }
    }
});

db.createCollection("system_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["action", "timestamp"],
            properties: {
                action: {
                    bsonType: "string",
                    description: "Action performed"
                },
                user_id: {
                    bsonType: ["int", "null"],
                    description: "User ID if applicable"
                },
                timestamp: {
                    bsonType: "date",
                    description: "When action occurred"
                }
            }
        }
    }
});

db.createCollection("conversion_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object", 
            required: ["user_id", "original_file", "status", "timestamp"],
            properties: {
                user_id: {
                    bsonType: "int",
                    description: "User who performed conversion"
                },
                original_file: {
                    bsonType: "string",
                    description: "Original NetCDF filename"
                },
                csv_file: {
                    bsonType: ["string", "null"],
                    description: "Generated CSV filename"
                },
                status: {
                    bsonType: "string",
                    enum: ["success", "failed", "processing"],
                    description: "Conversion status"
                }
            }
        }
    }
});

db.createCollection("vector_metadata", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["index", "text", "created_at"],
            properties: {
                index: {
                    bsonType: "int",
                    description: "FAISS vector index position"
                },
                text: {
                    bsonType: "string",
                    description: "Original text content"
                },
                metadata: {
                    bsonType: "object",
                    description: "Additional metadata"
                }
            }
        }
    }
});

// Create indexes for performance
db.chat_logs.createIndex({"user_id": 1, "timestamp": -1});
db.chat_logs.createIndex({"timestamp": -1});
db.system_logs.createIndex({"action": 1, "timestamp": -1});
db.conversion_logs.createIndex({"user_id": 1, "timestamp": -1});
db.conversion_logs.createIndex({"status": 1});
db.vector_metadata.createIndex({"index": 1}, {unique: true});

// Insert sample data
db.chat_logs.insertMany([
    {
        user_id: 2,
        query: "Show me temperature profiles near the equator",
        response: "I found 12 ARGO float profiles near the equator with average surface temperature of 28.2°C",
        relevant_docs: [
            {text: "Temperature profiles show oceanic thermal structure", metadata: {topic: "temperature"}},
            {text: "ARGO floats measure temperature from surface to 2000m", metadata: {topic: "argo"}}
        ],
        timestamp: new Date()
    },
    {
        user_id: 2,
        query: "What are the nearest floats to coordinates -10°S, 68°E?",
        response: "The nearest active ARGO floats are Float 2901623 (15.2 km away) and Float 2901625 (42.8 km away)",
        relevant_docs: [
            {text: "ARGO float locations can be queried by coordinates", metadata: {topic: "location"}}
        ],
        timestamp: new Date()
    }
]);

db.system_logs.insertMany([
    {
        action: "user_login",
        user_id: 1,
        details: {username: "admin", role: "admin"},
        timestamp: new Date()
    },
    {
        action: "nc_conversion",
        user_id: 1,
        details: {filename: "R2901623_001.nc", status: "success"},
        timestamp: new Date()
    },
    {
        action: "chatbot_training_update",
        user_id: 1,
        details: {training_items: 5, category: "oceanography"},
        timestamp: new Date()
    }
]);

db.conversion_logs.insertMany([
    {
        user_id: 1,
        original_file: "R2901623_001.nc",
        csv_file: "R2901623_001.csv",
        status: "success",
        rows: 2048,
        columns: 12,
        timestamp: new Date()
    },
    {
        user_id: 1,
        original_file: "indian_ocean_floats.nc", 
        csv_file: "indian_ocean_floats.csv",
        status: "success", 
        rows: 5672,
        columns: 18,
        timestamp: new Date()
    }
]);

// Insert vector database metadata
db.vector_metadata.insertMany([
    {
        index: 0,
        text: "ARGO floats are autonomous profiling floats that collect temperature and salinity data",
        metadata: {category: "introduction", importance: "high"},
        created_at: new Date()
    },
    {
        index: 1,
        text: "Temperature profiles show thermal stratification with warm surface and cold deep waters",
        metadata: {category: "oceanography", parameter: "temperature"},
        created_at: new Date()
    },
    {
        index: 2,
        text: "Salinity profiles indicate salt content measured in Practical Salinity Units PSU",
        metadata: {category: "oceanography", parameter: "salinity"},
        created_at: new Date()
    },
    {
        index: 3,
        text: "Indian Ocean ARGO network monitors monsoon effects and thermohaline circulation",
        metadata: {category: "regional", region: "indian_ocean"},
        created_at: new Date()
    }
]);

// Create TTL index for automatic cleanup of old logs (optional)
db.chat_logs.createIndex({"timestamp": 1}, {expireAfterSeconds: 31536000}); // 1 year
db.system_logs.createIndex({"timestamp": 1}, {expireAfterSeconds: 7776000}); // 90 days

print("MongoDB setup completed successfully!");
print("Collections created: " + db.getCollectionNames().length);
print("Sample data inserted for testing");
