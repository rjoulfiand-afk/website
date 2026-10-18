@extends('layouts.app', ['title' => 'Pusat Panduan Format Dokumen - Rapikan'])

@section('content')
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Pusat Modul Panduan Aplikasi</h1>
            <p class="text-xs text-gray-500 mt-1">
                Panduan teknis resmi langkah demi langkah untuk menyusun, merapikan, dan memperbaiki naskah laporan & skripsi pada Microsoft Word, Excel, dan Google Docs.
            </p>
        </div>
        <a href="/" class="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1">
            <span>&larr;</span>
            <span>Kembali ke Halaman Utama</span>
        </a>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        @forelse ($modules as $module)
            <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:border-blue-300 hover:shadow-md transition flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                            {{ $module->app_target }}
                        </span>
                        <span class="text-[11px] text-gray-400">
                            {{ $module->app_version_verified }}
                        </span>
                    </div>

                    <h3 class="text-base font-bold text-gray-900 mb-2">
                        <a href="{{ route('guides.show', $module->slug) }}" class="hover:text-blue-600">
                            {{ $module->title }}
                        </a>
                    </h3>

                    <p class="text-xs text-gray-600 line-clamp-3 leading-relaxed mb-4">
                        {{ $module->definition }}
                    </p>
                </div>

                <div class="pt-3 border-t border-gray-100 flex items-center justify-between">
                    <span class="text-[11px] text-gray-400">
                        Diverifikasi: {{ $module->verified_at ? $module->verified_at->format('M Y') : 'Terbaru' }}
                    </span>
                    <a 
                        href="{{ route('guides.show', $module->slug) }}" 
                        class="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                    >
                        <span>Baca Panduan</span>
                        <span>&rarr;</span>
                    </a>
                </div>
            </div>
        @empty
            <div class="col-span-full bg-white rounded-xl p-12 text-center border border-gray-200">
                <p class="text-sm text-gray-500">Belum ada modul panduan yang dipublikasikan.</p>
            </div>
        @endforelse
    </div>
</div>
@endsection
