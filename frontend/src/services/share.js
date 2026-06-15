import { creation } from './creation'

export const share = {
  view: (token) => creation.shareView(token),
  download: (token, format) => creation.dlByToken(token, format),
}
