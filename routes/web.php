<?php

use App\Http\Controllers\DocumentDownloadController;
use App\Http\Controllers\GuideModuleController;
use App\Livewire\ReportPage;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('upload');
})->name('home');

Route::get('/documents/{id}', ReportPage::class)->name('report.show');
Route::get('/documents/{id}/download-fixed/{fixLogId?}', [DocumentDownloadController::class, 'downloadFixed'])->name('documents.download-fixed');

// Modul Panduan (Requirement 5 & 6)
Route::get('/panduan', [GuideModuleController::class, 'index'])->name('guides.index');
Route::get('/panduan/{slug}', [GuideModuleController::class, 'show'])->name('guides.show');
