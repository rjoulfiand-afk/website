<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('guide_modules', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('slug', 100)->unique();
            $table->string('app_target', 20); // word, excel, gdocs, gsheets, gforms
            $table->string('title', 255);
            $table->text('definition');
            $table->text('when_to_use');
            $table->text('how_to_use');
            $table->text('how_to_remove');
            $table->text('how_to_fix');
            $table->text('common_mistakes');
            $table->text('example_before');
            $table->text('example_after');
            $table->string('app_version_verified', 50)->default('Word 365 (2024)');
            $table->date('verified_at')->nullable();
            $table->boolean('is_published')->default(true);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('guide_modules');
    }
};
