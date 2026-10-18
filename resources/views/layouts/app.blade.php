<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ $title ?? 'Rapikan - Perapian & Pemeriksaan Naskah Laporan/Skripsi' }}</title>
    <!-- Tailwind CSS CDN for lightweight standalone rendering -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        [x-cloak] { display: none !important; }
    </style>
    @livewireStyles
</head>
<body class="bg-gray-50 text-gray-900 min-h-screen flex flex-col font-sans antialiased">
    <!-- Navbar -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-sm">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <a href="/" class="flex items-center space-x-2">
                    <span class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-sm">R</span>
                    <span class="text-xl font-bold tracking-tight text-gray-900">Rapikan</span>
                </a>
                <span class="text-xs bg-emerald-50 text-emerald-700 font-medium px-2 py-0.5 rounded border border-emerald-200">Fase 2 Aktif</span>
            </div>

            <nav class="flex items-center space-x-6 text-sm font-medium text-gray-600">
                <a href="/" class="hover:text-blue-600 transition">Unggah Dokumen</a>
                <span class="text-gray-300">|</span>
                <a href="/panduan" class="hover:text-blue-600 transition">Modul Panduan</a>
                <span class="text-gray-400 cursor-not-allowed" title="Tersedia di Fase 3">Profil Kampus</span>
            </nav>
        </div>
    </header>

    <!-- Main Content -->
    <main class="flex-grow max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {{ $slot ?? '' }}
        @yield('content')
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 py-6 text-center text-xs text-gray-500">
        <div class="max-w-6xl mx-auto px-4">
            <p>&copy; {{ date('Y') }} Rapikan. Web perapian dan pemeriksaan dokumen skripsi & laporan ilmiah.</p>
            <p class="mt-1 text-gray-400">Deteksi berbasis isi berkas (magic bytes) &bull; Model Internal (IR) seragam &bull; Bebas penimpaan berkas asli.</p>
        </div>
    </footer>

    @livewireScripts
</body>
</html>
