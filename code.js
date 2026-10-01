figma.showUI(__html__, { width: 320, height: 460 });

const GIF_SIGNATURES = ['GIF87a', 'GIF89a'];

function bytesToAscii(bytes, start, length) {
  let s = '';
  for (let i = 0; i < length; i++) s += String.fromCharCode(bytes[start + i]);
  return s;
}

function isGif(bytes) {
  if (!bytes || bytes.length < 6) return false;
  return GIF_SIGNATURES.indexOf(bytesToAscii(bytes, 0, 6)) !== -1;
}

// Rebuilds the GIF byte-for-byte, dropping the NETSCAPE2.0 application
// extension (the block that tells decoders to loop). No loop extension
// means every common decoder, including Figma's own, plays it once.
function stripGifLoop(bytes) {
  if (GIF_SIGNATURES.indexOf(bytesToAscii(bytes, 0, 6)) === -1) {
    throw new Error('Not a valid GIF file.');
  }

  const out = [];
  const pushRange = (start, end) => {
    for (let k = start; k < end; k++) out.push(bytes[k]);
  };

  let i = 6;
  pushRange(0, 6);

  // Logical screen descriptor (7 bytes), optionally followed by a global color table.
  const lsdPacked = bytes[i + 4];
  pushRange(i, i + 7);
  const hasGct = (lsdPacked & 0x80) !== 0;
  const gctSize = hasGct ? 3 * Math.pow(2, (lsdPacked & 0x07) + 1) : 0;
  i += 7;
  if (hasGct) {
    pushRange(i, i + gctSize);
    i += gctSize;
  }

  let hadLoop = false;

  while (i < bytes.length) {
    const marker = bytes[i];

    if (marker === 0x3b) {
      // Trailer.
      pushRange(i, i + 1);
      i += 1;
      break;
    }

    if (marker === 0x21) {
      // Extension introducer.
      const label = bytes[i + 1];

      if (label === 0xff) {
        // Application extension.
        const blockSize = bytes[i + 2];
        const idStart = i + 3;
        const appId = bytesToAscii(bytes, idStart, 8);
        const appAuth = bytesToAscii(bytes, idStart + 8, 3);
        let p = idStart + blockSize;
        while (bytes[p] !== 0) p += 1 + bytes[p];
        p += 1; // block terminator

        if (appId === 'NETSCAPE' && appAuth === '2.0') {
          hadLoop = true;
        } else {
          pushRange(i, p);
        }
        i = p;
        continue;
      }

      let p = i + 2;
      if (label === 0xf9 || label === 0x01) {
        // Graphic control (0xF9) or plain text (0x01) extension: fixed-size block first.
        const blockSize = bytes[p];
        p += 1 + blockSize;
      }
      while (bytes[p] !== 0) p += 1 + bytes[p];
      p += 1;
      pushRange(i, p);
      i = p;
      continue;
    }

    if (marker === 0x2c) {
      // Image descriptor, optional local color table, then LZW image data.
      const idPacked = bytes[i + 9];
      let p = i + 10;
      const hasLct = (idPacked & 0x80) !== 0;
      const lctSize = hasLct ? 3 * Math.pow(2, (idPacked & 0x07) + 1) : 0;
      p += lctSize;
      p += 1; // LZW minimum code size
      while (bytes[p] !== 0) p += 1 + bytes[p];
      p += 1;
      pushRange(i, p);
      i = p;
      continue;
    }

    throw new Error('Unrecognized GIF structure at byte ' + i + '.');
  }

  return { bytes: Uint8Array.from(out), changed: hadLoop };
}

// Inserts a NETSCAPE2.0 application extension with loop count 0 (infinite),
// placed right after the header/logical screen descriptor (+ global color
// table), which is where encoders conventionally put it. Does nothing if a
// loop extension is already present.
function addGifLoop(bytes) {
  if (GIF_SIGNATURES.indexOf(bytesToAscii(bytes, 0, 6)) === -1) {
    throw new Error('Not a valid GIF file.');
  }

  const probe = stripGifLoop(bytes);
  if (probe.changed) {
    return { bytes, changed: false }; // already loops
  }

  const lsdPacked = bytes[10];
  const hasGct = (lsdPacked & 0x80) !== 0;
  const gctSize = hasGct ? 3 * Math.pow(2, (lsdPacked & 0x07) + 1) : 0;
  const insertPos = 6 + 7 + gctSize;

  const ext = [
    0x21, 0xff, 0x0b,
    0x4e, 0x45, 0x54, 0x53, 0x43, 0x41, 0x50, 0x45, // "NETSCAPE"
    0x32, 0x2e, 0x30, // "2.0"
    0x03, 0x01, 0x00, 0x00, // sub-block: size 3, data [1, loop_lo=0, loop_hi=0] => infinite
    0x00, // block terminator
  ];

  const out = [];
  for (let k = 0; k < insertPos; k++) out.push(bytes[k]);
  for (const b of ext) out.push(b);
  for (let k = insertPos; k < bytes.length; k++) out.push(bytes[k]);

  return { bytes: Uint8Array.from(out), changed: true };
}

function transformGif(bytes, direction) {
  return direction === 'add' ? addGifLoop(bytes) : stripGifLoop(bytes);
}

function collectGifPaintNodes(root) {
  const results = [];
  const visit = (node) => {
    if ('fills' in node && Array.isArray(node.fills)) {
      node.fills.forEach((paint, index) => {
        if (paint.type === 'IMAGE' && paint.imageHash) {
          results.push({ node, index });
        }
      });
    }
    if ('children' in node) {
      for (const child of node.children) visit(child);
    }
  };
  visit(root);
  return results;
}

async function processSelection(direction) {
  const selection = figma.currentPage.selection;
  if (selection.length === 0) {
    figma.ui.postMessage({ type: 'error', message: 'Select a layer with a GIF fill first.' });
    return;
  }

  let matches = [];
  for (const node of selection) {
    matches = matches.concat(collectGifPaintNodes(node));
  }

  if (matches.length === 0) {
    figma.ui.postMessage({ type: 'error', message: 'No image fills found in the selection.' });
    return;
  }

  let converted = 0;
  let alreadyMatched = 0;
  let skipped = 0;

  for (const { node, index } of matches) {
    try {
      const paint = node.fills[index];
      const image = figma.getImageByHash(paint.imageHash);
      const bytes = await image.getBytesAsync();

      if (!isGif(bytes)) {
        skipped += 1;
        continue;
      }

      const { bytes: newBytes, changed } = transformGif(bytes, direction);
      if (!changed) {
        alreadyMatched += 1;
        continue;
      }

      const newImage = figma.createImage(newBytes);
      const newFills = node.fills.slice();
      newFills[index] = Object.assign({}, paint, { imageHash: newImage.hash });
      node.fills = newFills;
      converted += 1;
    } catch (err) {
      skipped += 1;
    }
  }

  figma.ui.postMessage({ type: 'selection-result', direction, converted, alreadyMatched, skipped });
}

async function applyBytesToSelection(bytes, direction, changed) {
  const targets = figma.currentPage.selection.filter((n) => 'fills' in n);

  if (targets.length === 0) {
    figma.ui.postMessage({
      type: 'error',
      message: 'Select a layer to apply the fill to, or choose Download instead.',
    });
    return;
  }

  const newImage = figma.createImage(bytes);
  for (const node of targets) {
    node.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash: newImage.hash }];
  }

  figma.ui.postMessage({ type: 'upload-applied', direction, count: targets.length, changed });
}

figma.ui.onmessage = async (message) => {
  if (message.type === 'process-selection') {
    await processSelection(message.direction === 'add' ? 'add' : 'remove');
    return;
  }

  if (message.type === 'process-upload') {
    try {
      const direction = message.direction === 'add' ? 'add' : 'remove';
      const bytes = new Uint8Array(message.bytes);
      const { bytes: newBytes, changed } = transformGif(bytes, direction);

      if (message.target === 'apply') {
        await applyBytesToSelection(newBytes, direction, changed);
      } else {
        figma.ui.postMessage({
          type: 'download-ready',
          direction,
          bytes: Array.from(newBytes),
          changed,
        });
      }
    } catch (err) {
      figma.ui.postMessage({ type: 'error', message: (err && err.message) || 'Could not process this GIF.' });
    }
    return;
  }
};

figma.root.setRelaunchData({ open: '' });
