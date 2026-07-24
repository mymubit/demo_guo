import { http } from '@/services/http'
import type { CommandRunSummary, DeliveryState } from '@/types/v3/domain'

function deliveryBase(projectId: string): string {
  return `/api/v3/projects/${projectId}/delivery/`
}

export type DeliveryCommandResult = {
  command_run: CommandRunSummary
}

export async function getDeliveryState(projectId: string): Promise<DeliveryState> {
  return http.get<DeliveryState>(deliveryBase(projectId))
}

export async function prepareDelivery(projectId: string): Promise<DeliveryCommandResult> {
  return http.post<DeliveryCommandResult>(`${deliveryBase(projectId)}prepare/`, {})
}

export async function exportDeliveryDocx(projectId: string): Promise<Blob> {
  return http.post<Blob>(
    `${deliveryBase(projectId)}export/docx/`,
    {},
    { rawResponse: true, responseType: 'blob' },
  )
}
