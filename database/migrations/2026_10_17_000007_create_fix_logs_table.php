<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('fix_logs', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('document_id')->constrained('documents')->cascadeOnDelete();
            $table->foreignUuid('finding_id')->constrained('findings')->cascadeOnDelete();
            $table->string('fixed_storage_path', 500);
            $table->json('change_summary');
            $table->timestamp('applied_at')->useCurrent();
            $table->boolean('reanalysis_clean')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('fix_logs');
    }
};
