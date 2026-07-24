import { http } from '@/services/http'
import type {
  ArtifactRollbackRequest,
  ArtifactVersion,
  ArtifactVersionList,
  RollbackArtifactKey,
} from '@/types/v3/domain'

function artifactsBase(projectId: string): string {
  return `/api/v3/projects/${projectId}/artifacts/`
}

export async function listArtifactVersions(
  projectId: string,
  artifactKey: RollbackArtifactKey,
): Promise<ArtifactVersionList> {
  return http.get<ArtifactVersionList>(artifactsBase(projectId), {
    params: { artifact_key: artifactKey },
  })
}

export async function rollbackArtifact(
  projectId: string,
  body: ArtifactRollbackRequest,
): Promise<ArtifactVersion> {
  return http.post<ArtifactVersion>(`${artifactsBase(projectId)}rollback/`, body)
}
