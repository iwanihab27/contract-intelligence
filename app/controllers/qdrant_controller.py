import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct,
    SparseVectorParams, SparseVector,
    Prefetch, FusionQuery, Fusion
)
from fastembed import SparseTextEmbedding
from sqlalchemy.orm import Session

from app.controllers.base_controller import BaseController
from app.core.config import Settings

logger = logging.getLogger(__name__)

class QdrantController(BaseController):
    def __init__(self, db: Session, settings: Settings):
        super().__init__(db, settings)
        self.client = QdrantClient(
            url=self.settings.QDRANT_URL,
            api_key=self.settings.QDRANT_API_KEY
        )
        self.collection = self.settings.QDRANT_COLLECTION_NAME
        self.sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

    def ensure_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config={"dense": VectorParams(size=1024, distance=Distance.COSINE)},
                sparse_vectors_config={"sparse": SparseVectorParams()}
            )
            logger.info(f"Created Qdrant collection: {self.collection}")

    def embed_sparse(self, texts: list[str]) -> list[SparseVector]:
        results = list(self.sparse_model.embed(texts))
        sparse_vectors = []
        for r in results:
            sparse_vectors.append(SparseVector(
                indices=r.indices.tolist(),
                values=r.values.tolist()
            ))
        return sparse_vectors

    def store_chunks(self, chunks: list, dense_vectors: list, sparse_vectors: list):
        points = []
        for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors):
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector={"dense": dense, "sparse": sparse},
                payload={
                    "chunk_id": chunk.id,
                    "contract_id": chunk.contract_id,
                    "text": chunk.text,
                    "section_title": chunk.section_title,
                    "parent_id": chunk.parent_id,
                }
            )
            points.append(point)
            chunk.qdrant_id = point_id

        self.client.upsert(collection_name=self.collection, points=points)
        self.db.commit()
        logger.info(f"Stored {len(points)} vectors in Qdrant")

    def search(self, dense_vector: list, query_text: str, limit: int = 10) -> list:
        sparse_vector = self.embed_sparse([query_text])[0]
        results = self.client.query_points(
            collection_name=self.collection,
            prefetch=[
                Prefetch(query=dense_vector, using="dense", limit=20),
                Prefetch(query=sparse_vector, using="sparse", limit=20),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit
        )
        return results.points