import { Injectable } from '@angular/core';
import { getFunctions, httpsCallable } from 'firebase/functions';
import { from } from 'rxjs';
import {
  getVertexAI,
  getGenerativeModel,
  VertexAIBackend,
  getAI,
} from '@angular/fire/ai';
import { getApp } from 'firebase/app';

@Injectable({
  providedIn: 'root',
})
export class AiService {
  private functions = getFunctions();

  private ai = getAI(getApp(), { backend: new VertexAIBackend() });

  generateContent(prompt: string) {
    const generateContent = httpsCallable(this.functions, 'generateContent');
    return from(generateContent({ prompt }));
  }

  // Wrap in an async function so you can use await
  async runImagen(prompt: string): Promise<string | null> {
    // To generate text output, call generateCo ntent with the text input
    const model = getGenerativeModel(this.ai, {
      model: 'imagen-3.0-generate-002',
      generationConfig: { responseMimeType: 'image/jpeg' },
    });
    const result = await model.generateContent(prompt);

    // If fewer images were generated than were requested,
    // then `filteredReason` will describe the reason they were filtered out
    if (
      result.response.candidates?.[0]?.content.parts.find(
        (part) => part.inlineData
      )
    ) {
      console.log(
        result.response.candidates?.[0]?.content.parts.find((part) => part)
      );
    }

    if (
      result.response.candidates?.[0]?.content.parts.find(
        (part) => part.inlineData
      ) == null
    ) {
      throw new Error('No images in the response.');
    }

    const image = result.response.candidates?.[0]?.content.parts.find(
      (part) => part.inlineData
    );

    console.log(image);

    const rawBase64 = image?.inlineData?.data; // your Base64 string
    const mimeType = image?.inlineData?.mimeType; // change as needed

    return `data:${mimeType};base64,${rawBase64}`;
  }
}
