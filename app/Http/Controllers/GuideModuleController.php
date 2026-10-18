<?php

namespace App\Http\Controllers;

use App\Models\GuideModule;
use Illuminate\Http\Request;
use Illuminate\View\View;

class GuideModuleController extends Controller
{
    /**
     * Display list of all guide modules grouped by target application.
     */
    public function index(Request $request): View
    {
        $modules = GuideModule::where('is_published', true)
            ->orderBy('app_target')
            ->orderBy('title')
            ->get();

        return view('guides.index', [
            'modules' => $modules,
        ]);
    }

    /**
     * Display a specific guide module.
     */
    public function show(string $slug): View
    {
        $module = GuideModule::where('slug', $slug)
            ->where('is_published', true)
            ->firstOrFail();

        return view('guides.show', [
            'module' => $module,
        ]);
    }
}
