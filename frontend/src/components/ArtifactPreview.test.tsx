import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ArtifactPreview } from './ArtifactPreview'

describe('ArtifactPreview', () => {
  const payload = {
    title: '逆袭人生',
    core_idea: '重生翻盘',
    theme_code: 'matrix',
    genre_matrix: { emotion: 'revenge', world: 'modern', audience_channel: 'female' },
  }

  it('shows readable preview by default with Chinese labels and enum values', () => {
    render(<ArtifactPreview payload={payload} />)

    const root = screen.getByTestId('artifact-preview')
    expect(within(root).getByRole('heading', { name: '产物预览' })).toBeInTheDocument()
    const readable = within(root).getByTestId('artifact-preview-readable')
    expect(within(readable).getByText('概要')).toBeInTheDocument()
    expect(within(readable).getByText('标题')).toBeInTheDocument()
    expect(within(readable).getByText('逆袭人生')).toBeInTheDocument()
    expect(within(readable).getByText('题材矩阵')).toBeInTheDocument()
    expect(within(readable).getByText('主情绪')).toBeInTheDocument()
    expect(within(readable).getByText('复仇爽感')).toBeInTheDocument()
    expect(within(readable).getByText('都市现代')).toBeInTheDocument()
    expect(within(readable).getByText('女频')).toBeInTheDocument()
    expect(within(readable).queryByText('theme_code')).not.toBeInTheDocument()
    expect(within(readable).queryByText('revenge')).not.toBeInTheDocument()
    expect(screen.queryByTestId('artifact-preview-json')).not.toBeInTheDocument()
  })

  it('switches to formatted raw JSON', async () => {
    const user = userEvent.setup()
    render(<ArtifactPreview payload={payload} />)

    await user.click(screen.getByRole('button', { name: '原始 JSON' }))
    const jsonBlock = screen.getByTestId('artifact-preview-json')
    expect(jsonBlock.textContent).toContain('"title": "逆袭人生"')
    expect(jsonBlock.textContent).toMatch(/\n/)
  })
})
