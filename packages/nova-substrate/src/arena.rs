pub const ARENA_SIZE: usize = 1_048_576;
pub const MIN_ARENAS: usize = 4;

pub struct Arena {
    buf: Vec<u8>,
    cursor: usize,
}

impl Arena {
    pub fn new() -> Self {
        Self {
            buf: vec![0u8; ARENA_SIZE],
            cursor: 0,
        }
    }

    pub fn alloc(&mut self, size: usize) -> Option<&mut [u8]> {
        if self.cursor + size > ARENA_SIZE {
            return None;
        }
        let start = self.cursor;
        self.cursor += size;
        Some(&mut self.buf[start..start + size])
    }

    pub fn reset(&mut self) {
        self.cursor = 0;
    }

    pub fn capacity(&self) -> usize {
        ARENA_SIZE - self.cursor
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn arena_alloc_and_reset() {
        let mut arena = Arena::new();
        let slice = arena.alloc(16).expect("alloc 16 bytes");
        assert_eq!(slice.len(), 16);
        assert_eq!(arena.capacity(), ARENA_SIZE - 16);
        arena.reset();
        assert_eq!(arena.capacity(), ARENA_SIZE);
    }
}
