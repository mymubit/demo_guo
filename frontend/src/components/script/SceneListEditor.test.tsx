import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeAll, describe, expect, it, vi } from 'vitest'

import type { ScriptScene } from '@/types/v3/domain'

import { SceneListEditor } from './SceneListEditor'

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

const sampleScenes: ScriptScene[] = [
  {
    id: 's1',
    heading: 'INT. 咖啡厅 - 日',
    beats: [
      { type: 'action', text: '她推门而入' },
      { type: 'dialogue', text: '你好', character: '小美' },
    ],
  },
]

function pastePlainText(editor: HTMLElement, plain: string) {
  const clipboardData = {
    getData: (type: string) => (type === 'text/plain' ? plain : ''),
    types: ['text/plain'],
  }
  fireEvent.paste(editor, { clipboardData })
}

describe('SceneListEditor', () => {
  it('renders empty state with add scene button', () => {
    render(<SceneListEditor scenes={[]} onChange={() => {}} />)

    expect(screen.getByText('暂无场景，可新增一场开始编辑。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '新增场次' })).toBeInTheDocument()
  })

  it('renders heading, character, and BeatTiptap toolbar per beat', async () => {
    render(<SceneListEditor scenes={sampleScenes} onChange={() => {}} />)

    expect(screen.getByDisplayValue('INT. 咖啡厅 - 日')).toBeInTheDocument()
    expect(screen.getByLabelText('第 1 场对白角色')).toHaveValue('小美')

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: '动作文本' })).toHaveTextContent('她推门而入')
      expect(screen.getByRole('textbox', { name: '对白文本' })).toHaveTextContent('你好')
    })

    expect(screen.getAllByRole('button', { name: '粗体' })).toHaveLength(2)
    expect(screen.getByRole('button', { name: '加动作' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '加对白' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '新增场次' })).toBeInTheDocument()
  })

  it('updates beat text via BeatTiptap onChange', async () => {
    const onChange = vi.fn()
    render(<SceneListEditor scenes={sampleScenes} onChange={onChange} />)

    const actionEditor = await screen.findByRole('textbox', { name: '动作文本' })
    await act(async () => {
      pastePlainText(actionEditor, '新动作描述')
    })

    await waitFor(() => {
      expect(onChange).toHaveBeenCalled()
    })

    const lastScenes = onChange.mock.calls.at(-1)?.[0] as ScriptScene[]
    expect(lastScenes[0]?.beats[0]?.text).toContain('新动作描述')
  })

  it('adds scene and beats', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<SceneListEditor scenes={sampleScenes} onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: '加动作' }))
    const afterAddBeat = onChange.mock.calls.at(-1)?.[0] as ScriptScene[]
    expect(afterAddBeat[0]?.beats).toHaveLength(3)
    expect(afterAddBeat[0]?.beats[2]?.type).toBe('action')

    await user.click(screen.getAllByRole('button', { name: '新增场次' })[0]!)
    const afterAddScene = onChange.mock.calls.at(-1)?.[0] as ScriptScene[]
    expect(afterAddScene).toHaveLength(2)
    expect(afterAddScene[1]?.beats[0]?.type).toBe('action')
  })

  it('disables controls when disabled', async () => {
    render(<SceneListEditor scenes={sampleScenes} onChange={() => {}} disabled />)

    expect(screen.getByDisplayValue('INT. 咖啡厅 - 日')).toBeDisabled()
    expect(screen.getByLabelText('第 1 场对白角色')).toBeDisabled()
    expect(screen.getByRole('button', { name: '加动作' })).toBeDisabled()

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: '动作文本' })).toHaveAttribute(
        'contenteditable',
        'false',
      )
    })
  })
})
