import { http } from '@/services/http'
import type { SystemConfigPutRequest, SystemConfigState } from '@/types/v3/domain'

const SYSTEM_CONFIG_PATH = '/api/v3/system/config/'

export async function getSystemConfig(): Promise<SystemConfigState> {
  return http.get<SystemConfigState>(SYSTEM_CONFIG_PATH)
}

export async function putSystemConfig(body: SystemConfigPutRequest): Promise<SystemConfigState> {
  return http.put<SystemConfigState>(SYSTEM_CONFIG_PATH, body)
}
