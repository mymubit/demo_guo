import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeAll, describe, expect, it, vi } from 'vitest'

import { BeatTiptap } from './BeatTiptap'

beforeAll(() => {
  document.elementFromPoint = () => null
  Range.prototype.getBoundingClientRect = () =>
    ({
      x: 0,
      y: 0,
      width: 0,
      height: 0,
      top: 0,
      left: 0,
      bottom: 0,
      right: 0,
      toJSON: () => ({}),
    }) as DOMRect
  Range.prototype.getClientRects = () =>
    ({
      length: 0,
      item: () => null,
      [Symbol.iterator]: function* () {},
    }) as DOMRectList
})

function pastePlainText(editor: HTMLElement, plain: string, html = '') {
  const clipboardData = {
    getData: (type: string) => {
      if (type === 'text/plain') return plain
      if (type === 'text/html') return html
      return ''
    },
    types: html ? ['text/html', 'text/plain'] : ['text/plain'],
  }
  fireEvent.paste(editor, { clipboardData })
}

describe('BeatTiptap', () => {
  it('renders Chinese toolbar for bold/italic/heading/lists', () => {
    render(<BeatTiptap value="" onChange={() => {}} />)

    expect(screen.getByRole('button', { name: '粗体' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '斜体' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '标题' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '列表' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '有序列表' })).toBeInTheDocument()
  })

  it('calls onChange with plain text only (no HTML)', async () => {
    const onChange = vi.fn()

    render(<BeatTiptap value="" onChange={onChange} aria-label="节拍正文" />)

    const editor = screen.getByRole('textbox', { name: '节拍正文' })
    await act(async () => {
      pastePlainText(editor, '你好世界')
    })

    await waitFor(() => {
      expect(onChange).toHaveBeenCalled()
    })

    const lastCall = onChange.mock.calls.at(-1)?.[0] as string
    expect(typeof lastCall).toBe('string')
    expect(lastCall).toContain('你好世界')
    expect(lastCall).not.toMatch(/<[^>]+>/)
  })

  it('disables toolbar and editor when disabled', () => {
    render(<BeatTiptap value="已有内容" onChange={() => {}} disabled aria-label="节拍正文" />)

    expect(screen.getByRole('button', { name: '粗体' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '斜体' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '标题' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '列表' })).toBeDisabled()
    expect(screen.getByRole('button', { name: '有序列表' })).toBeDisabled()

    const editor = screen.getByRole('textbox', { name: '节拍正文' })
    expect(editor).toHaveAttribute('contenteditable', 'false')
  })

  it('strips HTML on paste and emits plain text via onChange', async () => {
    const onChange = vi.fn()
    render(<BeatTiptap value="" onChange={onChange} aria-label="节拍正文" />)

    const editor = screen.getByRole('textbox', { name: '节拍正文' })
    await act(async () => {
      pastePlainText(editor, '粘贴内容', '<p><strong>粘贴</strong><em>内容</em></p>')
    })

    await waitFor(() => {
      expect(onChange).toHaveBeenCalled()
    })

    const lastCall = onChange.mock.calls.at(-1)?.[0] as string
    expect(lastCall).toContain('粘贴内容')
    expect(lastCall).not.toMatch(/<[^>]+>/)
  })

  it('shows initial value as editor text', async () => {
    render(<BeatTiptap value="初始节拍" onChange={() => {}} aria-label="节拍正文" />)

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: '节拍正文' })).toHaveTextContent('初始节拍')
    })
  })
})
