import React from 'react';
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
          Bug-to-Task-Graph Pipeline
        </h1>
        <p className="max-w-xl mt-5 mx-auto text-xl text-gray-500">
          Track, manage, and convert bugs into actionable task graphs for efficient resolution.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link href="/bugs" className="btn btn-primary">
            View All Bugs
          </Link>
          <Link href="/bugs/create" className="btn btn-secondary">
            Report New Bug
          </Link>
        </div>
      </div>
      
      <div className="mt-20 grid gap-8 md:grid-cols-3">
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
          <div className="flex items-center justify-center h-12 w-12 rounded-md bg-primary text-white">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="mt-5 text-lg font-medium text-gray-900">Bug Tracking</h3>
          <p className="mt-2 text-base text-gray-500">
            Easily create, view, and manage bugs with detailed information and attachment support.
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
          <div className="flex items-center justify-center h-12 w-12 rounded-md bg-secondary text-white">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
            </svg>
          </div>
          <h3 className="mt-5 text-lg font-medium text-gray-900">Multimodal Attachments</h3>
          <p className="mt-2 text-base text-gray-500">
            Support for text, image, and PDF attachments with automatic processing and content extraction.
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
          <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-600 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="mt-5 text-lg font-medium text-gray-900">Task Graph Generation</h3>
          <p className="mt-2 text-base text-gray-500">
            Automatically convert bug reports into structured task graphs for systematic resolution.
          </p>
        </div>
      </div>
    </div>
  );
}
