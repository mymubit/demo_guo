import { describe, expect, it, vi } from 'vitest'

const { adminRequestMock } = vi.hoisted(() => ({
  adminRequestMock: vi.fn(),
}))

vi.mock('./http', () => ({
  adminRequest: adminRequestMock,
  unwrapAdminList: (data) => data,
}))

import { adminLibrary } from './library'

describe('adminLibrary.upload', () => {
  it('posts to upload endpoint with progress callback', async () => {
    adminRequestMock.mockResolvedValue({ data: { code: 0 } })
    const formData = new FormData()
    const onUploadProgress = vi.fn()
    await adminLibrary.upload(formData, { onUploadProgress })
    expect(adminRequestMock).toHaveBeenCalledWith(
      'POST',
      '/api/admin/creation/library/materials/upload/',
      expect.objectContaining({
        data: formData,
        onUploadProgress,
      }),
    )
  })
})
