<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('documents', function (Blueprint $table) {
            $table->string('genre')->default('auto')->after('campus_profile_id');
            $table->string('genre_detected')->nullable()->after('genre');
            $table->float('genre_confidence')->nullable()->after('genre_detected');
            $table->json('genre_markers')->nullable()->after('genre_confidence');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('documents', function (Blueprint $table) {
            $table->dropColumn(['genre', 'genre_detected', 'genre_confidence', 'genre_markers']);
        });
    }
};
