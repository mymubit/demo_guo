import { http } from '@/services/http'
import type { ModelPriceTable, ModelPriceTableWrite } from '@/types/v3/domain'

const PRICES_PATH = '/api/v3/models/prices/'

export async function getModelPrices(): Promise<ModelPriceTable> {
  return http.get<ModelPriceTable>(PRICES_PATH)
}

export async function putModelPrices(body: ModelPriceTableWrite): Promise<ModelPriceTable> {
  return http.put<ModelPriceTable>(PRICES_PATH, body)
}

export async function deleteModelPrice(
  priceId: number,
): Promise<{ deleted: boolean; id: number }> {
  return http.delete<{ deleted: boolean; id: number }>(`${PRICES_PATH}${priceId}/`)
}
