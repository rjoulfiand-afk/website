@extends('layouts.app', ['title' => $module->title . ' - Modul Panduan Rapikan'])

@section('content')
<div class="max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
        <a href="{{ route('guides.index') }}" class="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1">
            <span>&larr;</span>
            <span>Kembali ke Daftar Panduan</span>
        </a>

        <div class="flex items-center space-x-2 text-xs text-gray-500">
            <span>Aplikasi: <strong class="text-gray-700">{{ $module->app_version_verified }}</strong></span>
            <span>&bull;</span>
            <span>Status: <strong class="{{ $module->verified_at ? 'text-emerald-700' : 'text-amber-600' }}">{{ $module->verified_at ? 'Terverifikasi (' . $module->verified_at->format('d M Y') . ')' : 'Belum diverifikasi' }}</strong></span>
        </div>
    </div>

    <!-- Main Card -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 space-y-6">
        <div>
            <span class="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-1 rounded">
                {{ $module->app_target }}
            </span>
            <h1 class="text-2xl font-extrabold text-gray-900 mt-2 tracking-tight">
                {{ $module->title }}
            </h1>
        </div>

        <div class="space-y-6 text-sm text-gray-700 divide-y divide-gray-100">
            <!-- 1. Definisi -->
            <div class="pt-4">
                <h3 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-2">1. Definisi</h3>
                <p class="leading-relaxed text-gray-800">{{ $module->definition }}</p>
            </div>

            <!-- 2. Kapan Dipakai -->
            <div class="pt-4">
                <h3 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-2">2. Kapan Dipakai</h3>
                <p class="leading-relaxed text-gray-800">{{ $module->when_to_use }}</p>
            </div>

            <!-- 3. Cara Pakai -->
            <div class="pt-4">
                <h3 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-2">3. Cara Pakai (Standar Resmi Word/Docs)</h3>
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-200 whitespace-pre-line leading-relaxed text-gray-800">
                    {{ $module->how_to_use }}
                </div>
            </div>

            <!-- 4. Cara Hapus -->
            <div class="pt-4">
                <h3 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-2">4. Cara Hapus / Batalkan Format</h3>
                <p class="leading-relaxed text-gray-800">{{ $module->how_to_remove }}</p>
            </div>

            <!-- 5. Cara Merapikan -->
            <div class="pt-4">
                <h3 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-2">5. Cara Merapikan & Memperbaiki Masalah</h3>
                <div class="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200 whitespace-pre-line leading-relaxed text-emerald-950">
                    {{ $module->how_to_fix }}
                </div>
            </div>

            <!-- 6. Kesalahan Umum -->
            <div class="pt-4">
                <h3 class="text-xs font-bold uppercase tracking-wider text-red-900 mb-2">6. Kesalahan Umum yang Sering Terjadi</h3>
                <div class="bg-red-50/60 p-4 rounded-xl border border-red-200 text-red-900 leading-relaxed">
                    {{ $module->common_mistakes }}
                </div>
            </div>

            <!-- 7. Contoh Sebelum & Sesudah -->
            <div class="pt-4">
                <h3 class="text-xs font-bold uppercase tracking-wider text-blue-900 mb-3">7. Contoh Sebelum & Sesudah</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-4 rounded-xl bg-red-50/70 border border-red-200">
                        <span class="text-[11px] font-bold text-red-800 uppercase tracking-wider block mb-1.5">Sebelum (Keliru / Tidak Sesuai Standar):</span>
                        <pre class="font-mono text-xs text-red-900 whitespace-pre-wrap leading-relaxed">{{ $module->example_before }}</pre>
                    </div>

                    <div class="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200">
                        <span class="text-[11px] font-bold text-emerald-800 uppercase tracking-wider block mb-1.5">Sesudah (Benar / Mengikuti Pedoman):</span>
                        <pre class="font-mono text-xs text-emerald-900 whitespace-pre-wrap leading-relaxed">{{ $module->example_after }}</pre>
                    </div>
                </div>
            </div>

            <!-- 8. Metadata Verifikasi -->
            <div class="pt-4 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-gray-500 gap-2">
                <div>
                    Modul Panduan: <span class="font-mono font-semibold text-gray-700">{{ $module->slug }}</span>
                </div>
                <div>
                    Status: <strong class="{{ $module->verified_at ? 'text-gray-800' : 'text-amber-600' }}">{{ $module->verified_at ? 'Diverifikasi pada ' . $module->verified_at->format('d F Y') : 'Belum diverifikasi' }}</strong> pada <strong class="text-gray-800">{{ $module->app_version_verified }}</strong>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection
