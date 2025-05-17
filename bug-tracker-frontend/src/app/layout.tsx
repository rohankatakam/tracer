import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Bug Tracker - Task Graph Pipeline',
  description: 'Track and manage bugs for the Task Graph Pipeline',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-gray-50`}>
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-primary">Bug Tracker</h1>
              </div>
              <nav className="flex space-x-4">
                <a href="/" className="text-gray-600 hover:text-primary px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </a>
                <a href="/bugs" className="text-gray-600 hover:text-primary px-3 py-2 rounded-md text-sm font-medium">
                  Bugs
                </a>
                <a href="/bugs/create" className="text-gray-600 hover:text-primary px-3 py-2 rounded-md text-sm font-medium">
                  Create Bug
                </a>
              </nav>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
      </body>
    </html>
  )
}
