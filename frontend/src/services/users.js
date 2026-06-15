import { request } from './http'

export const users = {
  me() {
    return request('GET', '/api/users/me/')
  },
  updateMe(patchData) {
    return request('PUT', '/api/users/me/update/', { data: patchData })
  },
  updateProfile(profile) {
    const payload = {}
    if (profile.nickname !== undefined) payload.nickname = profile.nickname
    if (profile.avatar !== undefined) payload.avatar_url = profile.avatar
    if (profile.avatar_url !== undefined) payload.avatar_url = profile.avatar_url
    if (profile.bio !== undefined) payload.bio = profile.bio
    if (profile.gender !== undefined) payload.gender = profile.gender
    return this.updateMe(payload)
  },
  changePassword({ old_password, new_password, new_password_confirm }) {
    return request('POST', '/api/users/me/change_password/', {
      data: { old_password, new_password, new_password_confirm },
    })
  },
}
