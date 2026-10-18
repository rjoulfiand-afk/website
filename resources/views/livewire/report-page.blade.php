<div class="space-y-6">
    <!-- Breadcrumb & Actions -->
    <div class="flex items-center justify-between">
        <a href="/" class="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center space-x-1">
            <span>&larr;</span>
            <span>Kembali ke Halaman Unggah</span>
        </a>

        <div class="flex items-center space-x-2">
            <button 
                wire:click="reanalyze" 
                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 shadow-sm"
            >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Analisis Ulang Dokumen</span>
            </button>
        </div>
    </div>

    <!-- Global Fix Alerts -->
    @if ($globalFixSuccess)
        <div class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl shadow-sm flex items-start justify-between">
            <div class="flex items-start space-x-3">
                <svg class="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <div>
                    <h4 class="font-bold text-sm text-emerald-900">Perapian Selesai Berhasil!</h4>
                    <p class="text-xs text-emerald-800 mt-0.5">{{ $globalFixSuccess }}</p>
                </div>
            </div>
            <button wire:click="$set('globalFixSuccess', null)" class="text-emerald-700 hover:text-emerald-900 font-bold">&times;</button>
        </div>
    @endif

    @if ($globalFixError)
        <div class="p-4 bg-red-50 border border-red-200 text-red-900 rounded-xl shadow-sm flex items-start justify-between">
            <div class="flex items-start space-x-3">
                <svg class="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
                <div>
                    <h4 class="font-bold text-sm text-red-900">Gagal Melakukan Perapian (Rollback Dilakukan)</h4>
                    <p class="text-xs text-red-800 mt-0.5">{{ $globalFixError }}</p>
                </div>
            </div>
            <button wire:click="$set('globalFixError', null)" class="text-red-700 hover:text-red-900 font-bold">&times;</button>
        </div>
    @endif

    <!-- Document Header Info Card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <div class="flex items-center space-x-2.5">
                    <h1 class="text-xl font-bold text-gray-900 tracking-tight">
                        {{ $document->original_filename }}
                    </h1>
                    <span class="px-2 py-0.5 text-xs font-semibold rounded uppercase tracking-wider bg-gray-100 text-gray-700 border border-gray-200">
                        {{ $document->file_type->value }}
                    </span>
                    @if ($document->genre)
                        <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200" title="{{ $document->genre->description() }}">
                            Genre: {{ $document->genre->label() }}
                            @if ($document->genre_confidence)
                                ({{ round($document->genre_confidence * 100) }}%)
                            @endif
                        </span>
                    @endif
                    <span class="px-2.5 py-0.5 text-xs font-bold rounded-full {{ $document->status === \App\Enums\JobStatus::DONE ? 'bg-emerald-100 text-emerald-800' : ($document->status === \App\Enums\JobStatus::PROCESSING ? 'bg-blue-100 text-blue-800 animate-pulse' : 'bg-gray-100 text-gray-800') }}">
                        {{ $document->status->label() }}
                    </span>
                </div>
                @if ($document->genre_markers && count($document->genre_markers) > 0)
                    <div class="mt-2 text-xs text-indigo-700 bg-indigo-50/60 rounded px-2.5 py-1 border border-indigo-100 flex items-center space-x-1.5">
                        <span class="font-bold">Indikator Genre:</span>
                        <span>{{ implode(' • ', array_slice($document->genre_markers, 0, 3)) }}</span>
                    </div>
                @endif
                <p class="mt-1 text-xs text-gray-500">
                    ID Berkas: <span class="font-mono text-gray-700">{{ $document->id }}</span> &bull; Ukuran: {{ round($document->file_size_bytes / 1024, 1) }} KB &bull; Diperiksa: {{ $document->created_at->format('d M Y, H:i') }}
                </p>
            </div>

            <!-- Run Selector -->
            @if ($document->analysisRuns->count() > 1)
                <div class="flex items-center space-x-2 bg-gray-50 p-2 rounded-lg border border-gray-200">
                    <span class="text-xs font-bold text-gray-600">Pemeriksaan:</span>
                    <select 
                        wire:change="selectRun($event.target.value)" 
                        class="text-xs border-gray-300 rounded font-medium py-1 px-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        @foreach ($document->analysisRuns as $run)
                            <option value="{{ $run->id }}" {{ $currentRun && $currentRun->id === $run->id ? 'selected' : '' }}>
                                Run #{{ $run->run_number }} ({{ $run->created_at->format('H:i:s') }}) - {{ $run->findings_count }} temuan
                            </option>
                        @endforeach
                    </select>
                </div>
            @endif
        </div>

        <!-- Campus Profile Banner -->
        @if ($document->campusProfile)
            <div class="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
                <div class="text-xs text-gray-600">
                    Profil Acuan: <span class="font-semibold text-gray-900">{{ $document->campusProfile->name }}</span> (v{{ $document->campusProfile->version }})
                </div>

                @if (!$document->campusProfile->verified)
                    <div class="inline-flex items-center space-x-1.5 px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded text-xs font-medium" title="Pedoman resmi belum diverifikasi penuh">
                        <svg class="w-4 h-4 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                        </svg>
                        <span>Peringatan: Profil format ini belum diverifikasi dengan pedoman resmi kampus</span>
                    </div>
                @else
                    <span class="inline-flex items-center text-xs text-emerald-700 font-medium">
                        &check; Terverifikasi Sesuai Pedoman {{ $document->campusProfile->guideline_year }}
                    </span>
                @endif
            </div>
        @endif
    </div>

    <!-- Pre-flight Warning: Tracked Changes & Comments (Requirement 3) -->
    @if ($hasRevisionsOrComments)
        <div class="bg-amber-50 rounded-xl border-2 border-amber-300 p-5 shadow-sm flex items-start space-x-3.5">
            <div class="p-1.5 bg-amber-500 text-white rounded-lg flex-shrink-0 mt-0.5">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
            </div>
            <div class="text-xs text-amber-950 flex-grow">
                <h4 class="font-bold text-sm text-amber-900 tracking-tight flex items-center space-x-2">
                    <span>Peringatan Pre-Flight: Dokumen Mengandung Revisi atau Komentar Aktif</span>
                </h4>
                <p class="mt-1 leading-relaxed text-amber-900">
                    Dokumen ini terdeteksi memiliki revisi terlacak (<em>Track Changes</em> / markup) atau komentar. 
                    <strong>Sangat disarankan untuk menerima atau menolak seluruh revisi serta menyelesaikan komentar di Microsoft Word terlebih dahulu</strong> sebelum menjalankan perapian otomatis, guna mencegah ketidaksesuaian struktur.
                </p>
                <p class="mt-1 text-[11px] text-amber-800 font-medium">
                    &bull; Paragraf yang mengandung revisi atau komentar akan dilewati secara aman demi menjaga integritas naskah.
                </p>
            </div>
        </div>
    @endif

    <!-- Safe Mechanical Auto-Fix Action Card (Invariant 3 Compliance) -->
    @if ($autoFixableCount > 0)
        <div class="bg-gradient-to-r from-emerald-50 via-teal-50 to-blue-50 rounded-xl border border-emerald-200 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-1">
                <div class="flex items-center space-x-2">
                    <span class="p-1 bg-emerald-600 text-white rounded-lg">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </span>
                    <h3 class="text-sm font-bold text-gray-900">
                        Perapian Format Otomatis Aman ({{ $autoFixableCount }} Temuan)
                    </h3>
                </div>
                <p class="text-xs text-gray-600 max-w-2xl">
                    Sistem dapat langsung merapikan format Word (heading resmi, header tabel berulang, normalisasi spasi ganda, dan baris enter berlebih) menggunakan style Word semantik. <strong>Isi teks naskah tidak diubah</strong> dan berkas asli tidak pernah ditimpa.
                </p>
            </div>

            <button 
                wire:click="applyAllSafeFixes" 
                wire:loading.attr="disabled"
                class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition flex items-center justify-center space-x-2 shadow-sm whitespace-nowrap"
            >
                <svg wire:loading.remove wire:target="applyAllSafeFixes" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <svg wire:loading wire:target="applyAllSafeFixes" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Rapikan Format Sekaligus</span>
            </button>
        </div>
    @endif

    <!-- Rewrite Proposals Notice (Invariant 3) -->
    @if ($rewriteProposalsCount > 0)
        <div class="bg-amber-50 rounded-xl border border-amber-200 p-4 shadow-sm flex items-start space-x-3">
            <svg class="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
            <div class="text-xs text-amber-900">
                <h4 class="font-bold text-xs uppercase tracking-wide">Tersedia {{ $rewriteProposalsCount }} Usulan Penulisan Kata Baku (KBBI)</h4>
                <p class="mt-0.5 leading-relaxed">
                    Sesuai Invarian 3, perubahan susunan kata/ejaan <strong>tidak pernah dijalankan secara massal</strong> demi menjaga keaslian naskah. Tinjau usulan sebelum/sesudah dan setujui satu per satu melalui tombol <em>"Setujui Usulan Kata"</em> pada daftar temuan di bawah.
                </p>
            </div>
        </div>
    @endif

    <!-- Download Fixed Document Banner (If available) -->
    @if ($latestFixLog)
        <div class="bg-white rounded-xl border-2 border-emerald-500/40 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 flex-shrink-0">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </div>
                <div>
                    <h3 class="text-sm font-bold text-gray-900">
                        Dokumen Hasil Perapian Siap Diunduh
                    </h3>
                    <p class="text-xs text-gray-500">
                        Diterapkan: {{ $latestFixLog->applied_at->format('d M Y, H:i') }} &bull; Perubahan: {{ $latestFixLog->change_summary['fixes_applied'] ?? 0 }} perbaikan aman terverifikasi bersih &bull; File asli tetap utuh.
                    </p>
                </div>
            </div>

            <a 
                href="{{ route('documents.download-fixed', [$document->id, $latestFixLog->id]) }}" 
                class="px-4 py-2 bg-gray-900 hover:bg-black text-white rounded-lg text-xs font-bold transition flex items-center justify-center space-x-2 shadow-sm whitespace-nowrap"
            >
                <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Unduh Dokumen Rapi (.docx)</span>
            </a>
        </div>
    @endif

    <!-- Summary Stat Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <!-- Total Findings -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 text-center">
            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Total Temuan</span>
            <span class="text-2xl font-extrabold text-gray-900 mt-1 block">
                {{ $currentRun ? $currentRun->findings_count : $document->findings()->count() }}
            </span>
        </div>

        <!-- Errors -->
        <div class="bg-red-50 rounded-xl shadow-sm border border-red-200 p-4 text-center">
            <span class="text-xs font-semibold text-red-600 uppercase tracking-wider block">Kesalahan</span>
            <span class="text-2xl font-extrabold text-red-700 mt-1 block">
                {{ $currentRun ? $currentRun->error_count : $document->findings()->where('severity', 'error')->count() }}
            </span>
        </div>

        <!-- Warnings -->
        <div class="bg-yellow-50 rounded-xl shadow-sm border border-yellow-200 p-4 text-center">
            <span class="text-xs font-semibold text-yellow-700 uppercase tracking-wider block">Peringatan</span>
            <span class="text-2xl font-extrabold text-yellow-800 mt-1 block">
                {{ $currentRun ? $currentRun->warning_count : $document->findings()->where('severity', 'warning')->count() }}
            </span>
        </div>

        <!-- Info -->
        <div class="bg-blue-50 rounded-xl shadow-sm border border-blue-200 p-4 text-center">
            <span class="text-xs font-semibold text-blue-600 uppercase tracking-wider block">Informasi</span>
            <span class="text-2xl font-extrabold text-blue-700 mt-1 block">
                {{ $currentRun ? $currentRun->info_count : $document->findings()->where('severity', 'info')->count() }}
            </span>
        </div>

        <!-- Fixed Count -->
        <div class="bg-emerald-50 rounded-xl shadow-sm border border-emerald-200 p-4 text-center">
            <span class="text-xs font-semibold text-emerald-600 uppercase tracking-wider block">Diperbaiki</span>
            <span class="text-2xl font-extrabold text-emerald-700 mt-1 block">
                {{ $fixedCount }}
            </span>
        </div>

        <!-- Paragraphs Count -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 text-center">
            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Paragraf</span>
            <span class="text-2xl font-extrabold text-gray-900 mt-1 block">
                {{ $document->paragraphs_count ?? '-' }}
            </span>
        </div>
    </div>

    <!-- Findings List Component -->
    <livewire:findings-list :document-id="$document->id" :run-id="$currentRun?->id" :key="$currentRun?->id ?? 'initial'" />
</div>
