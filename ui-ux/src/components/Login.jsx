import { useState } from "react";
import { useNavigate } from "react-router-dom";
const Login = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [userName, setUserName] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const navigation = useNavigate();
    const handleLogin = async () => {
        const data = {
            username: userName,
            password: password,
        };
        console.log(data);
        try {
            setErrorMessage("");
            const res = await fetch(
                `${import.meta.env.VITE_API_URL}auth/login`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                },
            );
            const result = await res.json();
            if (result.success) {
                localStorage.setItem("token", result.token);
                navigation("/home");
            } else {
                setErrorMessage("Tài khoản hoặc mật khẩu không đúng.");
            }
        } catch (error) {
            console.error("Lỗi gửi dữ liệu:", error);
        }
    };
    return (
        <div className="min-h-screen bg-[#212121] flex justify-center items-center px-5 py-14">
            <div className="w-full max-w-[360px]">
                <img src="/public/logo.webp" />

                <div className="mt-10">
                    <label className="mb-3 block text-[16px] font-medium text-[#5f5f5f]">
                        Email
                    </label>
                    <input
                        value={userName}
                        onChange={(e) => setUserName(e.target.value)}
                        type="email"
                        defaultValue="balamia@gmail.com"
                        className="h-[58px] w-full rounded-[12px] border-2 border-[#b9d9ff] bg-white px-4 text-[16px] text-[#5a5a5a] outline-none"
                    />
                </div>

                <div className="mt-7">
                    <label className="mb-3 block text-[16px] font-medium text-[#5f5f5f]">
                        Password
                    </label>

                    <div className="relative">
                        <input
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            type={showPassword ? "text" : "password"}
                            placeholder="Enter your password"
                            className="h-[58px] w-full rounded-[12px] border border-[#d8d8d8] bg-white px-4 pr-14 text-[16px] text-[#5a5a5a] outline-none placeholder:text-[#c7c7c7]"
                        />

                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-[#bcbcbc]"
                        >
                            {showPassword ? (
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    className="h-6 w-6"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth="1.8"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M3 3l18 18M10.58 10.58A2 2 0 0013.42 13.42M9.88 4.24A10.94 10.94 0 0112 4c5 0 9.27 3.11 11 8a11.82 11.82 0 01-4.29 5.19M6.61 6.61A11.95 11.95 0 001 12s4 8 11 8a10.97 10.97 0 005.39-1.39"
                                    />
                                </svg>
                            ) : (
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    className="h-6 w-6"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth="1.8"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                                    />
                                    <circle cx="12" cy="12" r="3" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>

                <button
                    className="mt-10 h-[54px] w-full rounded-[10px] bg-[#0d80f2] text-[16px] font-semibold text-white shadow-sm transition hover:bg-[#0a74de]"
                    onClick={handleLogin}
                >
                    Đăng nhập
                </button>
                {errorMessage && (
                    <p
                        className="flex justify-center"
                        style={{ color: "red", marginTop: "10px" }}
                    >
                        {errorMessage}
                    </p>
                )}
            </div>
        </div>
    );
};
export default Login;
