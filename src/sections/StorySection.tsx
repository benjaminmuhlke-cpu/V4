const stats = [
  { number: '25+', label: '年的戶外經驗' },
  { number: '25+', label: '精選品牌' },
  { number: '100%', label: '嚴格測試認證' },
];

export default function StorySection() {
  return (
    <section className="bg-earth-dark px-8 py-24">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-16 items-start">
        <div className="flex flex-col gap-10">
          {stats.map(({ number, label }) => (
            <div key={label}>
              <div className="font-display text-5xl font-black text-earth-amber leading-none">
                {number}
              </div>
              <div className="text-earth-stone text-xs tracking-[0.2em] uppercase mt-2">
                {label}
              </div>
            </div>
          ))}
        </div>

        <div className="md:col-span-2">
          <p className="text-earth-amber text-xs tracking-[0.3em] uppercase mb-3">關於我們</p>
          <h2 className="font-display text-4xl md:text-5xl text-cream mb-8 leading-tight">
            對戶外的熱情，<br />從未改變
          </h2>
          <p className="text-earth-stone text-lg leading-relaxed mb-5">
            楞先生是一間由對戶外充滿熱情的人所經營的<strong className="text-cream font-semibold">家族商店</strong>。二十五年來，我們為各種探險者提供真正需要的裝備——從週末健行者到資深登山好手。
          </p>
          <p className="text-earth-stone text-lg leading-relaxed mb-5">
            架上每一個品牌，都經過我們<strong className="text-cream font-semibold">親身在各種天氣與環境中測試認證</strong>。我們只賣自己願意穿上身的裝備。
          </p>
          <p className="text-earth-stone text-lg leading-relaxed">
            無論是零下的山峰、颱風季的步道，還是多週的野外遠征，帶著你的挑戰來找我們，我們一定能為你<strong className="text-cream font-semibold">從頭到腳配備齊全</strong>。
          </p>
        </div>
      </div>
    </section>
  );
}
