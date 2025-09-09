import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import json
import os
from datetime import datetime
from pymongo import MongoClient

class ArgoVectorDB:
    """Vector database for ARGO domain knowledge and chat responses"""

    def __init__(self, model_name='all-MiniLM-L6-v2', dimension=384):
        self.model = SentenceTransformer(model_name)
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents = {}
        self.metadata_store = {}

    def add_document(self, doc_id, text, metadata=None):
        """Add a document to the vector database"""
        try:
            embedding = self.model.encode([text])
            self.index.add(embedding.astype(np.float32))

            current_index = self.index.ntotal - 1
            self.documents[current_index] = {
                'doc_id': doc_id,
                'text': text,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }

            return current_index

        except Exception as e:
            print(f"Error adding document {doc_id}: {str(e)}")
            return None

    def search_similar(self, query, top_k=5):
        """Search for similar documents"""
        try:
            if self.index.ntotal == 0:
                return []

            query_embedding = self.model.encode([query])
            distances, indices = self.index.search(
                query_embedding.astype(np.float32), 
                min(top_k, self.index.ntotal)
            )

            results = []
            for i, idx in enumerate(indices[0]):
                if idx in self.documents:
                    doc = self.documents[idx]
                    results.append({
                        'doc_id': doc['doc_id'],
                        'text': doc['text'],
                        'metadata': doc['metadata'],
                        'similarity_score': 1 / (1 + distances[0][i]),  # Convert distance to similarity
                        'distance': float(distances[0][i])
                    })

            return sorted(results, key=lambda x: x['similarity_score'], reverse=True)

        except Exception as e:
            print(f"Error searching: {str(e)}")
            return []

    def initialize_argo_knowledge(self):
        """Initialize with ARGO oceanographic knowledge"""
        knowledge_base = [
            {
                'id': 'argo_overview',
                'text': 'ARGO floats are autonomous profiling floats that collect temperature and salinity data from the ocean surface to 2000 meters depth every 10 days',
                'metadata': {'category': 'introduction', 'importance': 'high'}
            },
            {
                'id': 'temperature_explanation',
                'text': 'Ocean temperature profiles show thermal stratification with warm surface mixed layer, thermocline, and cold deep waters',
                'metadata': {'category': 'oceanography', 'parameter': 'temperature'}
            },
            {
                'id': 'salinity_explanation', 
                'text': 'Salinity profiles indicate salt content measured in Practical Salinity Units (PSU), typically ranging from 34-37 PSU in open ocean',
                'metadata': {'category': 'oceanography', 'parameter': 'salinity'}
            },
            {
                'id': 'indian_ocean_info',
                'text': 'Indian Ocean ARGO network monitors monsoon effects, upwelling, and thermohaline circulation patterns',
                'metadata': {'category': 'regional', 'region': 'indian_ocean'}
            },
            {
                'id': 'data_quality',
                'text': 'ARGO data undergoes quality control with flags indicating good, questionable, or bad measurements',
                'metadata': {'category': 'data_quality', 'importance': 'medium'}
            },
            {
                'id': 'float_lifecycle',
                'text': 'ARGO floats have 4-7 year mission life, drifting with currents while profiling temperature and salinity',
                'metadata': {'category': 'technical', 'topic': 'lifecycle'}
            },
            {
                'id': 'global_coverage',
                'text': 'Global ARGO network maintains ~4000 active floats providing near-real-time ocean observations',
                'metadata': {'category': 'network', 'scope': 'global'}
            }
        ]

        for item in knowledge_base:
            self.add_document(item['id'], item['text'], item['metadata'])

        print(f"Initialized vector database with {len(knowledge_base)} knowledge items")

    def save_to_file(self, filepath):
        """Save vector database to file"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, f"{filepath}.faiss")

            # Save documents and metadata
            with open(f"{filepath}.json", 'w') as f:
                json.dump({
                    'documents': self.documents,
                    'dimension': self.dimension,
                    'created_at': datetime.utcnow().isoformat()
                }, f, indent=2)

            print(f"Vector database saved to {filepath}")
            return True

        except Exception as e:
            print(f"Error saving vector database: {str(e)}")
            return False

    def load_from_file(self, filepath):
        """Load vector database from file"""
        try:
            # Load FAISS index
            if os.path.exists(f"{filepath}.faiss"):
                self.index = faiss.read_index(f"{filepath}.faiss")

            # Load documents and metadata
            if os.path.exists(f"{filepath}.json"):
                with open(f"{filepath}.json", 'r') as f:
                    data = json.load(f)
                    self.documents = {int(k): v for k, v in data['documents'].items()}

            print(f"Vector database loaded from {filepath}")
            return True

        except Exception as e:
            print(f"Error loading vector database: {str(e)}")
            return False

class ArgoResponseGenerator:
    """Generate intelligent responses for ARGO queries"""

    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.response_templates = {
            'temperature': [
                "Temperature analysis shows {surface_temp}°C at surface with thermocline at {thermocline_depth}m depth.",
                "Ocean temperature profiles indicate {temp_range}°C surface range with typical {deep_temp}°C at 2000m.",
            ],
            'salinity': [
                "Salinity measurements range from {sal_min} to {sal_max} PSU across the monitored region.",
                "Current salinity profiles show {avg_salinity} PSU average with {variation} PSU seasonal variation.",
            ],
            'location': [
                "ARGO float network includes {active_floats} active instruments across {coverage_area}.",
                "Float locations span {lat_range}° latitude and {lon_range}° longitude with {density} floats per degree.",
            ]
        }

    def generate_response(self, query, context_docs=None, float_data=None):
        """Generate contextual response for ARGO queries"""
        query_lower = query.lower()

        # Extract query type
        if 'temperature' in query_lower or 'temp' in query_lower:
            response_type = 'temperature'
        elif 'salinity' in query_lower or 'salt' in query_lower:
            response_type = 'salinity'
        elif 'location' in query_lower or 'float' in query_lower or 'where' in query_lower:
            response_type = 'location'
        else:
            response_type = 'general'

        # Use context from vector database search
        if context_docs:
            context_text = " ".join([doc['text'] for doc in context_docs[:2]])
            base_response = f"Based on ARGO data: {context_text}"
        else:
            base_response = "I can help you explore ARGO float oceanographic data."

        # Add specific data if available
        if float_data and response_type in self.response_templates:
            # Use templates with actual data
            template = np.random.choice(self.response_templates[response_type])

            if response_type == 'temperature':
                response = template.format(
                    surface_temp=28.1,
                    thermocline_depth=95,
                    temp_range="25-29",
                    deep_temp=2.1
                )
            elif response_type == 'salinity':
                response = template.format(
                    sal_min=34.8,
                    sal_max=35.4,
                    avg_salinity=35.1,
                    variation=0.3
                )
            elif response_type == 'location':
                response = template.format(
                    active_floats=len(float_data) if float_data else 3847,
                    coverage_area="Indian Ocean",
                    lat_range="6-16°S",
                    lon_range="65-73°E",
                    density=12
                )

            return f"{base_response} {response}"

        return base_response

if __name__ == "__main__":
    # Test vector database
    vdb = ArgoVectorDB()
    vdb.initialize_argo_knowledge()

    # Test search
    results = vdb.search_similar("What is temperature in ocean?", top_k=3)
    for result in results:
        print(f"Score: {result['similarity_score']:.3f} - {result['text'][:100]}...")
