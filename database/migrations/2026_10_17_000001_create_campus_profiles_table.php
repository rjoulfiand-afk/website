<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('campus_profiles', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('slug', 100)->unique();
            $table->string('name', 255);
            $table->string('version', 20)->default('1.0.0');
            $table->string('source_document', 255)->nullable();
            $table->unsignedSmallInteger('guideline_year')->nullable();
            $table->boolean('verified')->default(false);
            $table->text('rules_yaml')->nullable();
            $table->json('config');
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('campus_profiles');
    }
};
