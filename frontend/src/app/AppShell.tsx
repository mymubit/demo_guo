import { useState } from 'react'

import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { Clapperboard, LogOut, Menu, X } from 'lucide-react'

import { useAuth } from '@/auth/AuthContext'

import { Button } from '@/components/ui/Button'

import { cn } from '@/utils/cn'

import { V3_NAV_ITEMS } from './router'



function Navigation({ onNavigate }: { onNavigate: () => void }) {

  return (

    <nav className="space-y-1 px-3 py-5" aria-label="主导航">

      {V3_NAV_ITEMS.map((item) => (

        <NavLink

          key={item.to}

          to={item.to}

          end={item.to === '/dashboard'}

          onClick={onNavigate}

          className={({ isActive }) =>

            cn(

              'group flex items-center gap-3 rounded-md px-3 py-3 transition',

              isActive ? 'bg-[#e9f3ef] text-[#0f5c4b]' : 'text-slate-600 hover:bg-slate-100',

            )

          }

        >

          <span className="grid h-8 w-8 place-items-center rounded-md bg-slate-100 group-hover:bg-white">

            <item.icon className="h-4 w-4" />

          </span>

          <span>

            <span className="block text-sm font-semibold">{item.label}</span>

            <span className="mt-0.5 block text-[11px] text-slate-400">{item.hint}</span>

          </span>

        </NavLink>

      ))}

    </nav>

  )

}



export function AppShell() {

  const [open, setOpen] = useState(false)

  const { auth, logout } = useAuth()

  const navigate = useNavigate()



  async function handleLogout() {

    await logout()

    navigate('/login')

  }



  const sidebar = (

    <aside className="flex h-full flex-col bg-white text-slate-900">

      <div className="flex h-[76px] items-center gap-3 border-b border-slate-200 px-5">

        <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#0f5c4b] text-white">

          <Clapperboard className="h-4 w-4" />

        </div>

        <div>

          <div className="text-[15px] font-bold tracking-tight">ScriptForge</div>

          <div className="mt-0.5 text-[10px] font-medium uppercase tracking-[.16em] text-slate-400">

            创作工作台 · V3

          </div>

        </div>

      </div>

      <Navigation onNavigate={() => setOpen(false)} />

      <div className="mt-auto border-t border-slate-200 p-4">

        <div className="mb-3 truncate px-2 text-xs text-slate-500">

          {auth?.user?.nickname || auth?.user?.username || '当前用户'}

        </div>

        <Button

          variant="ghost"

          size="sm"

          className="w-full justify-start gap-2 text-slate-500"

          onClick={() => void handleLogout()}

          iconLeft={<LogOut className="h-4 w-4" />}

        >

          退出登录

        </Button>

      </div>

    </aside>

  )



  return (

    <div className="flex h-dvh min-h-[600px] bg-[#f6f8f7] text-slate-900">

      <aside className="hidden w-[252px] shrink-0 border-r border-slate-200 lg:block">{sidebar}</aside>

      {open ? (

        <div className="fixed inset-0 z-50 lg:hidden">

          <button

            type="button"

            className="absolute inset-0 bg-slate-900/30"

            aria-label="关闭菜单遮罩"

            onClick={() => setOpen(false)}

          />

          <aside className="relative h-full w-[280px] shadow-xl">

            {sidebar}

            <button

              type="button"

              className="absolute right-4 top-5 text-slate-500"

              onClick={() => setOpen(false)}

              title="关闭"

            >

              <X className="h-5 w-5" />

            </button>

          </aside>

        </div>

      ) : null}

      <section className="flex min-w-0 flex-1 flex-col">

        <header className="flex h-[68px] shrink-0 items-center border-b border-slate-200 bg-white px-4 sm:px-8">

          <button

            type="button"

            className="lg:hidden"

            onClick={() => setOpen(true)}

            title="打开菜单"

          >

            <Menu className="h-5 w-5" />

          </button>

        </header>

        <main className="min-h-0 flex-1 overflow-auto">

          <Outlet />

        </main>

      </section>

    </div>

  )

}


