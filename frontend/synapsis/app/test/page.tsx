"use client";

import { useState } from "react";

export default function TestPage() {
  const [count, setCount] = useState(0);
  
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-2xl font-bold">Test Page</h1>
      <p>If you can see this and interact, basic React is working.</p>
      <button 
        onClick={() => setCount(c => c + 1)}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        Count: {count}
      </button>
    </div>
  );
}
