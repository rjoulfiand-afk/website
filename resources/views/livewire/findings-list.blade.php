<div>
    <!-- Feedback / Fix Alerts -->
    @if ($feedbackSuccessMessage)
        <div class="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg flex items-center justify-between">
            <span>{{ $feedbackSuccessMessage }}</span>
            <button wire:click="$set('feedbackSuccessMessage', null)" class="text-emerald-600 hover:text-emerald-900 font-bold">&times;</button>
        </div>
    @endif

    @if ($fixSuccessMessage)
        <div class="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg flex items-center justify-between shadow-sm">
            <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <span class="font-medium">{{ $fixSuccessMessage }}</span>
            </div>
            <button wire:click="$set('fixSuccessMessage', null)" class="text-emerald-600 hover:text-emerald-900 font-bold">&times;</button>
        </div>
    @endif

    @if ($fixErrorMessage)
        <div class="mb-4 p-3 bg-red-50 border border-red-200 text-red-800 text-sm rounded-lg flex items-center justify-between">
            <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
                <span>{{ $fixErrorMessage }}</span>
            </div>
            <button wire:click="$set('fixErrorMessage', null)" class="text-red-600 hover:text-red-900 font-bold">&times;</button>
        </div>
    @endif

    <!-- Controls Bar -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <!-- Severity Filters -->
        <div class="flex flex-wrap items-center gap-1.5 sm:gap-2">
            <button 
                wire:click="setSeverity('all')" 
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition border {{ $severityFilter === 'all' ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50' }}"
            >
                Semua Temuan
            </button>
            <button 
                wire:click="setSeverity('error')" 
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition border {{ $severityFilter === 'error' ? 'bg-red-600 text-white border-red-600' : 'bg-white text-red-700 border-red-200 hover:bg-red-50' }}"
            >
                Kesalahan (Error)
            </button>
            <button 
                wire:click="setSeverity('warning')" 
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition border {{ $severityFilter === 'warning' ? 'bg-yellow-500 text-white border-yellow-500' : 'bg-white text-yellow-800 border-yellow-200 hover:bg-yellow-50' }}"
            >
                Peringatan (Warning)
            </button>
            <button 
                wire:click="setSeverity('info')" 
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition border {{ $severityFilter === 'info' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-blue-700 border-blue-200 hover:bg-blue-50' }}"
            >
                Informasi (Info)
            </button>
            <button 
                wire:click="toggleAutoFixable" 
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition border {{ $autoFixableOnly ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-emerald-700 border-emerald-200 hover:bg-emerald-50' }}"
            >
                Bisa Perapian Otomatis
            </button>
        </div>

        <!-- Search Input -->
        <div class="w-full md:w-64">
            <input 
                type="text" 
                wire:model.live.debounce.300ms="search" 
                placeholder="Cari aturan, teks, lokasi..." 
                class="w-full text-xs rounded-lg border border-gray-300 px-3 py-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
            >
        </div>
    </div>

    <!-- Findings Cards -->
    <div class="space-y-4">
        @forelse ($findings as $finding)
            <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:border-gray-300 transition {{ $finding->status === 'fixed' ? 'bg-emerald-50/30 border-emerald-200' : '' }}">
                <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div class="flex items-center space-x-2.5">
                        <!-- Severity Badge -->
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border {{ $finding->severity->badgeClass() }}">
                            {{ $finding->severity->label() }}
                        </span>

                        <span class="font-mono text-xs font-bold text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                            {{ $finding->rule_id }}
                        </span>

                        <h3 class="font-semibold text-gray-900 text-sm">
                            {{ $finding->rule_name }}
                        </h3>

                        @if ($finding->status === 'fixed')
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                                &check; Telah Diperbaiki
                            </span>
                        @endif
                    </div>

                    <!-- Location Pill -->
                    <div class="flex items-center space-x-2 text-xs text-gray-500">
                        <span class="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 font-medium text-gray-700">
                            {{ $finding->location_label }}
                        </span>
                        @if ($finding->page_estimate)
                            <span class="text-gray-400" title="Perkiraan nomor halaman dari LibreOffice">
                                (Hal. ~{{ $finding->page_estimate }})
                            </span>
                        @endif
                    </div>
                </div>

                <!-- Evidence Snippet -->
                <div class="mt-3 bg-gray-50 rounded-lg p-3 border border-gray-100 text-xs text-gray-700 font-mono">
                    <span class="font-bold text-gray-500 uppercase tracking-wider block text-[10px] mb-1">Bukti Saat Ini:</span>
                    <p class="whitespace-pre-wrap break-words">{{ $finding->evidence_current['snippet'] ?? json_encode($finding->evidence_current) }}</p>
                    @if (isset($finding->evidence_current['detail']))
                        <p class="mt-1 text-gray-500 font-sans text-[11px]">{{ $finding->evidence_current['detail'] }}</p>
                    @endif
                </div>

                <!-- Suggestion / Action -->
                <div class="mt-3 flex items-start space-x-2 text-xs text-gray-800">
                    <span class="font-bold text-blue-700 whitespace-nowrap">Saran Tindakan:</span>
                    <p class="flex-grow">{{ $finding->suggestion_text }}</p>
                </div>

                <!-- Footer details & actions -->
                <div class="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center justify-between text-xs text-gray-500 gap-2">
                    <div class="flex items-center space-x-3">
                        @if ($finding->rule_id === 'B002')
                            <span class="inline-flex items-center text-amber-800 bg-amber-50 px-2 py-0.5 rounded text-[11px] font-semibold border border-amber-200">
                                Usulan Kata Baku (Perlu Persetujuan)
                            </span>
                        @elseif ($finding->auto_fixable)
                            <span class="inline-flex items-center text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-semibold border border-emerald-200">
                                Perapian Format Otomatis
                            </span>
                        @else
                            <span class="inline-flex items-center text-gray-500 bg-gray-50 px-2 py-0.5 rounded text-[11px] font-medium border border-gray-200">
                                Panduan Manual
                            </span>
                        @endif

                        @if ($finding->guide_module_slug)
                            <button 
                                wire:click="openGuideModal('{{ $finding->guide_module_slug }}')" 
                                class="text-blue-600 hover:text-blue-800 underline font-medium inline-flex items-center space-x-1"
                                title="Buka modul panduan lengkap"
                            >
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                </svg>
                                <span>Panduan: {{ $finding->guide_module_slug }}</span>
                            </button>
                        @endif
                    </div>

                    <div class="flex items-center space-x-3">
                        <!-- Rewrite Proposal Approval (B002) -->
                        @if ($finding->rule_id === 'B002' && $finding->status !== 'fixed')
                            <button 
                                wire:click="applySingleFix('{{ $finding->id }}', true)" 
                                wire:loading.attr="disabled"
                                class="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold transition shadow-sm flex items-center space-x-1"
                                title="Setujui dan ganti kata ini pada salinan berkas"
                            >
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                <span>Setujui Usulan Kata</span>
                            </button>
                        <!-- Mechanical Auto-Fix Button (W001, W006, W008, W010) -->
                        @elseif ($finding->auto_fixable && $finding->status !== 'fixed')
                            <button 
                                wire:click="applySingleFix('{{ $finding->id }}', false)" 
                                wire:loading.attr="disabled"
                                class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold transition shadow-sm flex items-center space-x-1"
                            >
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                <span>Perbaiki Format</span>
                            </button>
                        @endif

                        <!-- False positive reporter button -->
                        <button 
                            wire:click="openFeedbackModal('{{ $finding->id }}')" 
                            class="text-gray-400 hover:text-red-600 text-xs transition"
                            title="Beri tahu sistem jika temuan ini tidak akurat"
                        >
                            Temuan ini salah?
                        </button>
                    </div>
                </div>
            </div>
        @empty
            <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <svg class="mx-auto h-12 w-12 text-emerald-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 class="text-base font-bold text-gray-900">Tidak Ada Temuan</h3>
                <p class="mt-1 text-xs text-gray-500">
                    Tidak ditemukan kesalahan format yang cocok dengan filter aktif saat ini.
                </p>
            </div>
        @endforelse
    </div>

    <!-- Pagination -->
    <div class="mt-6">
        {{ $findings->links() }}
    </div>

    <!-- Guide Module Modal (Requirement 5: 8 section template) -->
    @if ($activeGuideModule)
        <div class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-gray-200 max-h-[90vh] flex flex-col">
                <div class="flex items-center justify-between pb-3 border-b border-gray-200">
                    <div>
                        <span class="text-[11px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                            {{ $activeGuideModule->app_target }}
                        </span>
                        <h2 class="text-lg font-bold text-gray-900 mt-1">
                            {{ $activeGuideModule->title }}
                        </h2>
                    </div>
                    <button wire:click="closeGuideModal" class="text-gray-400 hover:text-gray-700 text-xl font-bold">&times;</button>
                </div>

                <div class="overflow-y-auto py-4 space-y-4 text-xs text-gray-700 flex-grow pr-2">
                    <!-- 1. Definisi -->
                    <div>
                        <h4 class="font-bold text-gray-900 uppercase text-[11px] tracking-wider mb-1 text-blue-900">1. Definisi</h4>
                        <p class="leading-relaxed">{{ $activeGuideModule->definition }}</p>
                    </div>

                    <!-- 2. Kapan Dipakai -->
                    <div>
                        <h4 class="font-bold text-gray-900 uppercase text-[11px] tracking-wider mb-1 text-blue-900">2. Kapan Dipakai</h4>
                        <p class="leading-relaxed">{{ $activeGuideModule->when_to_use }}</p>
                    </div>

                    <!-- 3. Cara Pakai -->
                    <div>
                        <h4 class="font-bold text-gray-900 uppercase text-[11px] tracking-wider mb-1 text-blue-900">3. Cara Pakai (Standar Resmi)</h4>
                        <div class="bg-gray-50 p-3 rounded-lg border border-gray-100 whitespace-pre-line leading-relaxed">{{ $activeGuideModule->how_to_use }}</div>
                    </div>

                    <!-- 4. Cara Hapus -->
                    <div>
                        <h4 class="font-bold text-gray-900 uppercase text-[11px] tracking-wider mb-1 text-blue-900">4. Cara Hapus / Batalkan</h4>
                        <p class="leading-relaxed">{{ $activeGuideModule->how_to_remove }}</p>
                    </div>

                    <!-- 5. Cara Merapikan -->
                    <div>
                        <h4 class="font-bold text-gray-900 uppercase text-[11px] tracking-wider mb-1 text-blue-900">5. Cara Merapikan / Memperbaiki</h4>
                        <div class="bg-emerald-50/50 p-3 rounded-lg border border-emerald-100 whitespace-pre-line leading-relaxed text-emerald-900">{{ $activeGuideModule->how_to_fix }}</div>
                    </div>

                    <!-- 6. Kesalahan Umum -->
                    <div>
                        <h4 class="font-bold text-gray-900 uppercase text-[11px] tracking-wider mb-1 text-red-900">6. Kesalahan Umum yang Sering Terjadi</h4>
                        <p class="leading-relaxed text-red-700">{{ $activeGuideModule->common_mistakes }}</p>
                    </div>

                    <!-- 7. Contoh Sebelum dan Sesudah -->
                    <div>
                        <h4 class="font-bold text-gray-900 uppercase text-[11px] tracking-wider mb-1 text-blue-900">7. Contoh Sebelum dan Sesudah</h4>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                            <div class="p-2.5 rounded bg-red-50 border border-red-200">
                                <span class="font-bold text-red-800 text-[10px] uppercase block mb-1">Sebelum (Salah / Tidak Baku):</span>
                                <pre class="font-mono text-[11px] text-red-900 whitespace-pre-wrap">{{ $activeGuideModule->example_before }}</pre>
                            </div>
                            <div class="p-2.5 rounded bg-emerald-50 border border-emerald-200">
                                <span class="font-bold text-emerald-800 text-[10px] uppercase block mb-1">Sesudah (Rapi / Baku):</span>
                                <pre class="font-mono text-[11px] text-emerald-900 whitespace-pre-wrap">{{ $activeGuideModule->example_after }}</pre>
                            </div>
                        </div>
                    </div>

                    <!-- 8. Versi Aplikasi dan Terakhir Diverifikasi -->
                    <div class="pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
                        <span>Aplikasi: <strong class="text-gray-700">{{ $activeGuideModule->app_version_verified }}</strong></span>
                        <span>Status: <strong class="{{ $activeGuideModule->verified_at ? 'text-gray-700' : 'text-amber-600' }}">{{ $activeGuideModule->verified_at ? 'Terverifikasi (' . $activeGuideModule->verified_at->format('d M Y') . ')' : 'Belum diverifikasi' }}</strong></span>
                    </div>
                </div>

                <div class="pt-3 border-t border-gray-200 flex justify-end">
                    <button 
                        wire:click="closeGuideModal" 
                        class="px-4 py-1.5 bg-gray-900 hover:bg-black text-white text-xs font-semibold rounded-lg"
                    >
                        Tutup Panduan
                    </button>
                </div>
            </div>
        </div>
    @endif

    <!-- False Positive Feedback Modal -->
    @if ($feedbackFindingId)
        <div class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-40 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-gray-200">
                <h3 class="text-base font-bold text-gray-900 mb-2">Laporkan Temuan Tidak Akurat</h3>
                <p class="text-xs text-gray-600 mb-4">
                    Bantu kami meningkatkan akurasi sistem. Mengapa menurut Anda temuan ini tidak sesuai atau keliru?
                </p>

                <textarea 
                    wire:model="feedbackReason" 
                    rows="3" 
                    placeholder="Contoh: Ini bukan heading melainkan kutipan langsung; font memang diperbolehkan berbeda untuk kode..." 
                    class="w-full text-xs rounded-lg border border-gray-300 p-2.5 focus:ring-blue-500 focus:border-blue-500"
                ></textarea>

                <div class="mt-4 flex justify-end space-x-2">
                    <button 
                        wire:click="$set('feedbackFindingId', null)" 
                        class="px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                    >
                        Batal
                    </button>
                    <button 
                        wire:click="submitFalsePositive" 
                        class="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-xs font-semibold text-white shadow-sm"
                    >
                        Kirim Laporan
                    </button>
                </div>
            </div>
        </div>
    @endif
</div>
