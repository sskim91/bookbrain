import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { uploadBook, type UploadBookResponse } from '@/api/books';
import { ApiError } from '@/api/client';

describe('uploadBook', () => {
  let mockXHRInstance: {
    open: ReturnType<typeof vi.fn>;
    send: ReturnType<typeof vi.fn>;
    setRequestHeader: ReturnType<typeof vi.fn>;
    upload: {
      addEventListener: ReturnType<typeof vi.fn>;
    };
    addEventListener: ReturnType<typeof vi.fn>;
    status: number;
    responseText: string;
  };

  beforeEach(() => {
    mockXHRInstance = {
      open: vi.fn(),
      send: vi.fn(),
      setRequestHeader: vi.fn(),
      upload: {
        addEventListener: vi.fn(),
      },
      addEventListener: vi.fn(),
      status: 200,
      responseText: '',
    };

    // Create a class constructor for XMLHttpRequest mock
    const MockXMLHttpRequest = vi.fn(function (this: typeof mockXHRInstance) {
      Object.assign(this, mockXHRInstance);
      return this;
    });

    vi.stubGlobal('XMLHttpRequest', MockXMLHttpRequest);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('should send file via FormData to correct endpoint', async () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const responseData: UploadBookResponse = {
      status: 'indexed',
      book_id: 1,
      chunks_count: 10,
    };

    mockXHRInstance.responseText = JSON.stringify(responseData);

    const uploadPromise = uploadBook(file);

    // Simulate load event
    const loadHandler = mockXHRInstance.addEventListener.mock.calls.find(
      (call) => call[0] === 'load'
    )?.[1];

    if (loadHandler) {
      loadHandler();
    }

    const result = await uploadPromise;

    expect(mockXHRInstance.open).toHaveBeenCalledWith(
      'POST',
      expect.stringContaining('/api/books')
    );
    expect(mockXHRInstance.send).toHaveBeenCalledWith(expect.any(FormData));
    expect(result).toEqual(responseData);
  });

  it('should call onProgress callback during upload', async () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });
    const onProgress = vi.fn();

    const responseData: UploadBookResponse = {
      status: 'indexed',
      book_id: 1,
      chunks_count: 10,
    };

    mockXHRInstance.responseText = JSON.stringify(responseData);

    const uploadPromise = uploadBook(file, { onProgress });

    // Simulate progress event
    const progressHandler =
      mockXHRInstance.upload.addEventListener.mock.calls.find(
        (call) => call[0] === 'progress'
      )?.[1];

    if (progressHandler) {
      progressHandler({ lengthComputable: true, loaded: 50, total: 100 });
    }

    // Simulate load event
    const loadHandler = mockXHRInstance.addEventListener.mock.calls.find(
      (call) => call[0] === 'load'
    )?.[1];

    if (loadHandler) {
      loadHandler();
    }

    await uploadPromise;

    expect(onProgress).toHaveBeenCalledWith(50);
  });

  it('should throw ApiError on server error response', async () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    mockXHRInstance.status = 400;
    mockXHRInstance.responseText = JSON.stringify({
      error: {
        code: 'INVALID_FILE_FORMAT',
        message: 'Only PDF files are allowed',
      },
    });

    const uploadPromise = uploadBook(file);

    // Simulate load event with error status
    const loadHandler = mockXHRInstance.addEventListener.mock.calls.find(
      (call) => call[0] === 'load'
    )?.[1];

    if (loadHandler) {
      loadHandler();
    }

    await expect(uploadPromise).rejects.toThrow(ApiError);
    await expect(uploadPromise).rejects.toMatchObject({
      code: 'INVALID_FILE_FORMAT',
      message: 'Only PDF files are allowed',
    });
  });

  it('should throw ApiError on network error', async () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const uploadPromise = uploadBook(file);

    // Simulate error event
    const errorHandler = mockXHRInstance.addEventListener.mock.calls.find(
      (call) => call[0] === 'error'
    )?.[1];

    if (errorHandler) {
      errorHandler();
    }

    await expect(uploadPromise).rejects.toThrow(ApiError);
    await expect(uploadPromise).rejects.toMatchObject({
      code: 'NETWORK_ERROR',
    });
  });

  it('should include title and author in FormData when provided', async () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    });

    const responseData: UploadBookResponse = {
      status: 'indexed',
      book_id: 1,
      chunks_count: 10,
    };

    mockXHRInstance.responseText = JSON.stringify(responseData);

    let capturedFormData: FormData | null = null;
    mockXHRInstance.send = vi.fn((data) => {
      capturedFormData = data;
    });

    const uploadPromise = uploadBook(file, {
      title: 'Test Book',
      author: 'Test Author',
    });

    // Simulate load event
    const loadHandler = mockXHRInstance.addEventListener.mock.calls.find(
      (call) => call[0] === 'load'
    )?.[1];

    if (loadHandler) {
      loadHandler();
    }

    await uploadPromise;

    expect(capturedFormData).toBeInstanceOf(FormData);
    expect(capturedFormData?.get('file')).toBe(file);
    expect(capturedFormData?.get('title')).toBe('Test Book');
    expect(capturedFormData?.get('author')).toBe('Test Author');
  });
});
