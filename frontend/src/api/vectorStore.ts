import { apiClient } from './config'

export interface VectorCollectionInfo {
  collection: string
  deleted: boolean
}

export interface ClearVectorStoreResult {
  deleted: string[]
  total: number
}

export interface ClearEmbeddingCacheResult {
  cache_dirs: string[]
  cleared: string[]
  errors: string[]
}

export interface ClearAllResult {
  vector_collections: { deleted?: string[]; total?: number; error?: string; skipped?: string }
  embedding_cache: { cleared?: string; error?: string; skipped?: string }
  chromadb_dir: { cleared?: string; error?: string; skipped?: string }
}

export const vectorStoreApi = {
  listCollections: () =>
    apiClient.get<string[]>('/admin/vector-store/collections') as unknown as Promise<string[]>,

  clearAll: () =>
    apiClient.delete<ClearVectorStoreResult>('/admin/vector-store/collections') as unknown as Promise<ClearVectorStoreResult>,

  deleteCollection: (collection: string) =>
    apiClient.delete<VectorCollectionInfo>(`/admin/vector-store/collections/${encodeURIComponent(collection)}`) as unknown as Promise<VectorCollectionInfo>,

  clearEmbeddingCache: () =>
    apiClient.delete<ClearEmbeddingCacheResult>('/admin/vector-store/embedding-cache') as unknown as Promise<ClearEmbeddingCacheResult>,

  clearAllWithCache: () =>
    apiClient.delete<ClearAllResult>('/admin/vector-store/all') as unknown as Promise<ClearAllResult>,
}
