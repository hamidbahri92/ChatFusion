import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import FormData from 'form-data';
import fs from 'fs';

export default async function handler(req, res) {
  if (req.method === 'POST') {
    const formData = new FormData();
    formData.append('user_message', req.body.user_message);

    if (req.files && req.files.image) {
      const image = await fs.promises.readFile(req.files.image.filepath);
      formData.append('image', image, req.files.image.originalFilename);
    }

    try {
      const response = await axios.post(`${process.env.API_URL}/chat`, formData, {
        headers: {
          ...formData.getHeaders(),
          Authorization: `Bearer ${process.env.SECRET_TOKEN}`,
        },
      });
      res.status(200).json(response.data);
    } catch (error) {
      res.status(500).json({ error: 'An error occurred while processing your request.' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed.' });
  }
}

export const config = {
  api: {
    bodyParser: false,
  },
};
