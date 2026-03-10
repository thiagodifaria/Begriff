import { useState } from "react";

export default function Login({ onLogin, authError }) {
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [localError, setLocalError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user || !pass) {
      setLocalError("Informe usuario e senha.");
      return;
    }
    setLocalError("");
    const ok = await onLogin(user, pass);
    if (!ok) setLocalError("Credenciais invalidas.");
  };

  return (
    <div className="relative flex h-screen bg-white font-sans text-gray-900 overflow-hidden">
      <div className="login-blob login-blob-a" />
      <div className="login-blob login-blob-b" />
      <div className="hidden md:flex w-1/2 bg-[#f5f4f2]/90 backdrop-blur-sm p-12 flex-col justify-between border-r border-gray-200">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight mb-2 login-fade-up">Begriff</h1>
          <p className="text-sm text-gray-500 max-w-sm leading-relaxed">
            Plataforma de Inteligencia Financeira Empresarial. Processamento hibrido de alta performance.
          </p>

          <div className="mt-16 space-y-4 text-sm text-gray-700">
            <div className="flex gap-3 items-center">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
              Pipeline Hibrido COBOL + C++ + Python
            </div>
            <div className="flex gap-3 items-center">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
              Deteccao de Fraude ML (Isolation Forest)
            </div>
            <div className="flex gap-3 items-center">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
              Auditoria SHA-256 + Blockchain Simulado
            </div>
          </div>
        </div>

        <div className="text-xs text-gray-500 font-mono tracking-tight">100k+ trans/s · &lt;50ms p99 · 99.99% uptime</div>
      </div>

      <div className="w-full md:w-1/2 flex items-center justify-center p-6 sm:p-12">
        <form onSubmit={handleSubmit} className="w-full max-w-xs bg-white/90 border border-gray-200 rounded-2xl p-6 sm:p-8 shadow-lg login-fade-up">
          <h2 className="text-xl font-semibold mb-8">Entrar</h2>

          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Usuario</label>
              <input
                type="text"
                value={user}
                onChange={(e) => setUser(e.target.value)}
                className="w-full border border-gray-300 rounded-md p-2 text-sm outline-none focus:border-gray-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Senha</label>
              <input
                type="password"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                className="w-full border border-gray-300 rounded-md p-2 text-sm outline-none focus:border-gray-500 transition-colors"
              />
            </div>
            {localError || authError ? <p className="text-xs text-red-600">{localError || authError}</p> : null}
          </div>

          <button
            type="submit"
            className="w-full bg-gray-900 text-white text-sm font-medium py-2 rounded-md hover:bg-gray-800 transition-all duration-300 hover:translate-y-[-1px]"
          >
            Acessar Plataforma
          </button>
        </form>
      </div>
    </div>
  );
}
