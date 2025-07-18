import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import {
  GenerativeModel,
  getGenerativeModel,
  AI,
  ImagenModel,
  getImagenModel,
} from '@angular/fire/ai';

@Component({
  selector: 'app-ai-test',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './ai-test.component.html',
  styleUrls: ['./ai-test.component.scss'],
})
export class AiTestComponent implements OnInit {
  imagenPrompt = '';
  generativePrompt = '';
  imagenResult = '';
  generativeResult = '';
  isLoading = false;
  isGeneratingImage = false;
  generatedImageUrl: string | null = null;
  ai = inject(AI);
  imagenModel!: ImagenModel;
  generativeModel!: GenerativeModel;

  ngOnInit() {
    this.imagenModel = getImagenModel(this.ai, {
      model: 'imagen-3.0-generate-002',
    });
    this.generativeModel = getGenerativeModel(this.ai, {
      model: 'gemini-2.0-flash',
    });
  }

  async runImagen(prompt: string) {
    this.isLoading = true;
    try {
      const result = await this.imagenModel.generateImages(prompt);
      if (result.filteredReason) {
        console.log(result.filteredReason);
      }
      if (result.images?.length === 0) {
        throw new Error('No images in the response.');
      }
      const image = result.images[0];
      const rawBase64 = image.bytesBase64Encoded;
      const mimeType = image.mimeType;
      this.imagenResult = `data:${mimeType};base64,${rawBase64}`;
    } catch (e) {
      console.error(e);
    } finally {
      this.isLoading = false;
    }
  }

  async run(prompt: string) {
    this.isLoading = true;
    this.generativeResult = '';
    this.generatedImageUrl = null;
    try {
      const result = await this.generativeModel.generateContent(prompt);
      this.generativeResult = result.response.text();
    } catch (e) {
      console.error(e);
    } finally {
      this.isLoading = false;
    }
  }

  async generateImageFromTextResult() {
    if (!this.generativeResult) return;
    this.isGeneratingImage = true;
    this.generatedImageUrl = null;
    try {
      const result = await this.imagenModel.generateImages(this.generativeResult);
      if (result.filteredReason) {
        console.log(result.filteredReason);
      }
      if (result.images?.length === 0) {
        throw new Error('No images in the response.');
      }
      const image = result.images[0];
      const rawBase64 = image.bytesBase64Encoded;
      const mimeType = image.mimeType;
      this.generatedImageUrl = `data:${mimeType};base64,${rawBase64}`;
    } catch (e) {
      console.error(e);
    } finally {
      this.isGeneratingImage = false;
    }
  }
}
