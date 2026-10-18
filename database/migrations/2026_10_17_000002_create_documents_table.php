<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('documents', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignId('user_id')->nullable()->constrained('users')->nullOnDelete();
            $table->string('original_filename', 255);
            $table->string('file_type', 20); // docx, xlsx, pdf, gdocs, gsheets, gforms
            $table->decimal('detection_confidence', 5, 4)->default(1.0);
            $table->string('storage_path', 500);
            $table->char('file_hash', 64);
            $table->unsignedBigInteger('file_size_bytes');
            $table->foreignUuid('campus_profile_id')->nullable()->constrained('campus_profiles')->nullOnDelete();
            $table->string('status', 20)->default('queued'); // queued, processing, done, failed
            $table->string('ir_path', 500)->nullable(); // Path to compressed JSON in storage
            $table->unsignedInteger('paragraphs_count')->nullable();
            $table->unsignedInteger('tables_count')->nullable();
            $table->char('text_hash', 64)->nullable();
            $table->boolean('llm_consent_given')->default(false);
            $table->timestamp('expires_at')->nullable();
            $table->timestamps();

            $table->index('file_hash');
            $table->index('status');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('documents');
    }
};
