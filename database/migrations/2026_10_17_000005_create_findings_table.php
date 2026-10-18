<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('findings', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('document_id')->constrained('documents')->cascadeOnDelete();
            $table->foreignUuid('analysis_run_id')->nullable()->constrained('analysis_runs')->cascadeOnDelete();
            $table->string('rule_id', 20);
            $table->string('rule_name', 255);
            $table->string('severity', 20); // error, warning, info
            $table->string('location_type', 30); // paragraph, section, cell, table, image, footer, document
            $table->string('location_id', 100);
            $table->string('location_label', 255);
            $table->unsignedSmallInteger('page_estimate')->nullable();
            $table->boolean('page_is_estimate')->default(true);
            $table->unsignedSmallInteger('section_index')->nullable();
            $table->json('evidence_current');
            $table->json('evidence_expected')->nullable();
            $table->text('suggestion_text');
            $table->boolean('auto_fixable')->default(false);
            $table->decimal('confidence', 5, 4)->default(1.0);
            $table->string('status', 30)->default('open'); // open, approved, rejected, fixed, false_positive
            $table->foreignUuid('guide_module_id')->nullable()->constrained('guide_modules')->nullOnDelete();
            $table->string('guide_module_slug', 100)->nullable();
            $table->boolean('llm_source')->default(false);
            $table->string('llm_paragraph_ref', 100)->nullable();
            $table->text('llm_quote')->nullable();
            $table->timestamp('created_at')->useCurrent();

            $table->index(['document_id', 'rule_id']);
            $table->index('severity');
            $table->index('status');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('findings');
    }
};
