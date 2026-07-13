import request from './request'

export const profileApi = {
  upload: (formData: FormData) =>
    request.post('/profile/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  analyze: (sourceId: number) => request.post(`/profile/${sourceId}/analyze`),

  getResult: (sourceId: number) => request.get(`/profile/${sourceId}`),

  listSources: (params?: any) => request.get('/profile/sources', { params }),
}
