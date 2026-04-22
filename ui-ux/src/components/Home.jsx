import { useEffect, useRef, useState } from "react";
import { SquarePen, Plus } from "lucide-react";

const Home = () => {
    const handleKeyDown = (e) => {
        if (e.nativeEvent.isComposing) return;

        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };
    const [message, setMessage] = useState("");
    const [chatStarted, setChatStarted] = useState(false);
    const [messages, setMessages] = useState([]);
    const handleSend = async () => {
        if (!message.trim()) return;

        const token = localStorage.getItem("token");
        const data = { text: message };
        const currentMessage = message;

        setMessages((prev) => [
            ...prev,
            { role: "user", text: currentMessage },
        ]);
        setChatStarted(true);
        setMessage("");

        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(data),
            });

            const result = await res.json();
            console.log(result);

            if (!res.ok || !result.success) {
                console.error("API lỗi:", result.message, result.error);
                return;
            }

            setMessages((prev) => [
                ...prev,
                { role: "assistant", text: result.reply },
            ]);
        } catch (error) {
            console.error("Lỗi gửi dữ liệu:", error);
        }
    };

    return (
        <div className="flex h-screen overflow-hidden bg-[#212121] text-white">
            <aside className="hidden md:flex h-screen w-[260px] flex-col border-r border-white/10 bg-[#0d0d0d] text-white">
                <div className="flex items-center justify-between px-4 py-3">
                    <div className="mb-3 mt-5">
                        <img src="/logo.webp" alt="logo" />
                    </div>
                </div>

                <div
                    className="px-3"
                    onClick={() => {
                        window.location.reload();
                    }}
                >
                    <button
                        type="button"
                        className="flex w-full items-center gap-3 rounded-xl bg-white/10 px-3 py-3 text-sm font-medium transition hover:bg-white/15"
                    >
                        <SquarePen size={18} />
                        Đoạn chat mới
                    </button>
                </div>
            </aside>

            <main
                className="
                    relative flex-1 overflow-y-auto
                    [&::-webkit-scrollbar]:w-1.25
                    [&::-webkit-scrollbar-track]:bg-transparent
                    [&::-webkit-scrollbar-thumb]:rounded-full
                    [&::-webkit-scrollbar-thumb]:bg-white/20
                    hover:[&::-webkit-scrollbar-thumb]:bg-white/30
                "
            >
                {!chatStarted && (
                    <h1 className="pointer-events-none absolute left-1/2 top-[22%] -translate-x-1/2 text-center text-5xl font-semibold tracking-tight transition-all duration-500">
                        Hôm nay bạn muốn hỏi gì?
                    </h1>
                )}

                {chatStarted && (
                    <div className="mx-auto w-full max-w-3xl px-4 pb-44 pt-8">
                        <div className="space-y-6">
                            {messages.map((msg, index) => (
                                <div
                                    key={index}
                                    className={`flex ${
                                        msg.role === "user"
                                            ? "justify-end"
                                            : "justify-start"
                                    }`}
                                >
                                    <div
                                        className={`max-w-[80%] rounded-2xl px-4 py-3 text-base ${
                                            msg.role === "user"
                                                ? "bg-white text-black"
                                                : "bg-[#2f2f2f] text-white"
                                        }`}
                                    >
                                        {msg.text}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div
                    className={`${
                        !chatStarted
                            ? "absolute left-1/2 w-full max-w-3xl -translate-x-1/2 px-6 transition-all duration-700 top-1/2 -translate-y-1/2"
                            : "mx-auto w-full max-w-3xl px-6"
                    }`}
                >
                {/* <div
                    className={`absolute left-1/2 w-full max-w-3xl -translate-x-1/2 px-6 transition-all duration-700 ease-in-out ${
                        chatStarted
                            ? "flex z-50 right-6 "
                            : "top-1/2 -translate-y-1/2"
                    }`}
                > */}
                    <div className="mx-auto w-full max-w-3xl">
                        <div className="rounded-[28px] border border-white/10 bg-[#2f2f2f] px-5 py-4 shadow-2xl">
                            <textarea
                                onKeyDown={handleKeyDown}
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder="Hỏi bất kỳ điều gì về bảo hiểm xã hội"
                                rows={1}
                                className="w-full resize-none bg-transparent text-lg text-white outline-none placeholder:text-white/50"
                            />

                            <div className="mt-4 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <button
                                        type="button"
                                        className="rounded-full p-2 text-white/80 transition hover:bg-white/10"
                                    >
                                        <Plus size={0} />
                                    </button>
                                </div>

                                <div className="flex items-center gap-3">
                                    <button
                                        type="button"
                                        onClick={handleSend}
                                        className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-black transition hover:scale-105"
                                    >
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            className="h-5 w-5"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                            strokeWidth="2.2"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                d="M5 12h14M13 6l6 6-6 6"
                                            />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Home;
