import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/utils/cn';

const maxWidthClasses = {
  sm: 'max-w-3xl',
  md: 'max-w-4xl',
  lg: 'max-w-6xl',
  xl: 'max-w-7xl',
  '2xl': 'max-w-[1600px]',
  full: 'max-w-full',
};

export default function PageShell({
  title,
  description,
  backTo,
  actions,
  children,
  className,
  maxWidth = 'xl',
  noPadding = false,
}) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (typeof backTo === 'function') {
      backTo();
    } else if (typeof backTo === 'string') {
      navigate(backTo);
    } else {
      navigate(-1);
    }
  };

  return (
    <div className={cn('min-h-screen flex flex-col bg-navy-950', className)}>
      <header className="sticky top-0 z-20 bg-navy-950/80 backdrop-blur-xl border-b border-white/5">
        <div className={cn('mx-auto px-4 sm:px-6 lg:px-8', maxWidthClasses[maxWidth])}>
          <div className="py-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-3">
                {backTo !== undefined && (
                  <button
                    type="button"
                    onClick={handleBack}
                    className="flex-shrink-0 flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-300 transition-all hover:bg-white/10 hover:text-white"
                    aria-label="返回"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                )}
                <div className="min-w-0">
                  <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight truncate">
                    {title}
                  </h1>
                  {description && (
                    <p className="mt-1 text-sm text-slate-400 truncate">{description}</p>
                  )}
                </div>
              </div>
            </div>
            {actions && (
              <div className="flex items-center gap-3 flex-shrink-0 flex-wrap justify-end">
                {actions}
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div
          className={cn(
            'mx-auto',
            maxWidthClasses[maxWidth],
            !noPadding && 'px-4 sm:px-6 lg:px-8 py-6 sm:py-8'
          )}
        >
          {children}
        </div>
      </main>
    </div>
  );
}
