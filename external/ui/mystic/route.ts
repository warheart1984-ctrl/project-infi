import { NextResponse } from "next/server";
import { mythicEngine } from "@/lib/mythic-engine";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const input = typeof body.input === "string" ? body.input.trim() : "";

    if (!input) {
      return NextResponse.json({ error: "Input is required." }, { status: 400 });
    }

    const reading = mythicEngine(input);
    return NextResponse.json({ reading });
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }
}