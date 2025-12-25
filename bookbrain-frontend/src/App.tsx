import { useState } from 'react';
import { MainLayout } from '@/components/MainLayout';
import { SearchInput } from '@/components/SearchInput';
import { SearchResultList } from '@/components/SearchResultList';
import type { SearchResultItem } from '@/types';

// Dummy data for UI testing - will be replaced with actual API call in Story 2.4
const DUMMY_RESULTS: SearchResultItem[] = [
  {
    book_id: 1,
    title: '토비의 스프링',
    author: '이일민',
    page: 423,
    content:
      'Spring Security는 인증(Authentication)과 권한 부여(Authorization)를 담당하는 프레임워크입니다. 기본적인 설정은 WebSecurityConfigurerAdapter를 상속받아 configure 메서드를 오버라이드하면 됩니다.',
    score: 0.92,
  },
  {
    book_id: 2,
    title: '클린 코드',
    author: '로버트 C. 마틴',
    page: 156,
    content:
      '함수는 한 가지를 해야 한다. 그 한 가지를 잘 해야 한다. 그 한 가지만을 해야 한다. 지정된 함수 이름 아래에서 추상화 수준이 하나인 단계만 수행한다면 그 함수는 한 가지 작업만 한다.',
    score: 0.87,
  },
  {
    book_id: 3,
    title: '도메인 주도 설계',
    author: '에릭 에반스',
    page: 89,
    content:
      'AGGREGATE는 데이터 변경의 단위로 다루는 연관 객체의 묶음이다. 각 AGGREGATE에는 루트(root)와 경계(boundary)가 있다. 경계는 AGGREGATE에 무엇이 포함되고 포함되지 않는지를 정의한다.',
    score: 0.78,
  },
];

function App() {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<SearchResultItem[]>([]);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);

    // TODO: Replace with actual API call in Story 2.4
    // Using dummy data for UI testing
    setTimeout(() => {
      setResults(DUMMY_RESULTS);
      setIsSearching(false);
    }, 500);
  };

  return (
    <MainLayout>
      <div className="w-full max-w-[800px] flex flex-col items-center pt-16">
        <SearchInput
          value={query}
          onChange={setQuery}
          onSearch={handleSearch}
          isLoading={isSearching}
          autoFocus={true}
        />
        <SearchResultList
          results={results}
          isLoading={isSearching}
          hasSearched={hasSearched}
        />
      </div>
    </MainLayout>
  );
}

export default App;
