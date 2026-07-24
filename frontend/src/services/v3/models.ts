import { http } from '@/services/http'
import type {
  ModelProvider,
  ModelProviderWrite,
  ProviderKey,
  ProviderKeyList,
  ProviderKeyWrite,
  ProviderTestResult,
  RoleModelMappingTable,
} from '@/types/v3/domain'

const PROVIDERS_PATH = '/api/v3/models/providers/'
const ROLE_MAPPINGS_PATH = '/api/v3/models/role-mappings/'

export type ModelProviderList = {
  items: ModelProvider[]
}

function providerPath(providerId: string): string {
  return `${PROVIDERS_PATH}${providerId}/`
}

export async function listProviders(): Promise<ModelProviderList> {
  return http.get<ModelProviderList>(PROVIDERS_PATH)
}

export async function getProvider(providerId: string): Promise<ModelProvider> {
  return http.get<ModelProvider>(providerPath(providerId))
}

export async function createProvider(body: ModelProviderWrite): Promise<ModelProvider> {
  return http.post<ModelProvider>(PROVIDERS_PATH, body)
}

export async function updateProvider(
  providerId: string,
  body: ModelProviderWrite,
): Promise<ModelProvider> {
  return http.patch<ModelProvider>(providerPath(providerId), body)
}

export async function deleteProvider(providerId: string): Promise<null> {
  return http.delete<null>(providerPath(providerId))
}

export async function activateProvider(providerId: string): Promise<ModelProvider> {
  return http.post<ModelProvider>(`${providerPath(providerId)}activate/`, {})
}

export async function testProvider(providerId: string): Promise<ProviderTestResult> {
  return http.post<ProviderTestResult>(`${providerPath(providerId)}test/`, {})
}

function providerKeysPath(providerId: string): string {
  return `${providerPath(providerId)}keys/`
}

export async function listProviderKeys(providerId: string): Promise<ProviderKeyList> {
  return http.get<ProviderKeyList>(providerKeysPath(providerId))
}

export async function createProviderKey(
  providerId: string,
  body: ProviderKeyWrite,
): Promise<ProviderKey> {
  return http.post<ProviderKey>(providerKeysPath(providerId), body)
}

export async function updateProviderKey(
  providerId: string,
  keyId: string,
  body: ProviderKeyWrite,
): Promise<ProviderKey> {
  return http.patch<ProviderKey>(`${providerKeysPath(providerId)}${keyId}/`, body)
}

export async function deleteProviderKey(providerId: string, keyId: string): Promise<null> {
  return http.delete<null>(`${providerKeysPath(providerId)}${keyId}/`)
}

export async function getRoleMappings(): Promise<RoleModelMappingTable> {
  return http.get<RoleModelMappingTable>(ROLE_MAPPINGS_PATH)
}

export async function putRoleMappings(
  body: RoleModelMappingTable,
): Promise<RoleModelMappingTable> {
  return http.put<RoleModelMappingTable>(ROLE_MAPPINGS_PATH, body)
}
