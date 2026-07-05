"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function AddressForm() {
  const router = useRouter();
  const [value, setValue] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = value.trim();
    if (q) router.push(`/report?address=${encodeURIComponent(q)}`);
  }

  return (
    <form className="search" onSubmit={submit}>
      <span aria-hidden>🔍</span>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="도로명·동·호수까지 정확히 입력하세요"
        aria-label="감정할 주소"
      />
      <button type="submit" className="go-btn" aria-label="감정하기">
        감정
      </button>
    </form>
  );
}
